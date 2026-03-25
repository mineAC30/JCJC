"""
設定ファイルローダー

YAML ファイルから各パラメータ dataclass を構築する。
configs/ ディレクトリの *.yaml を読み込み、
domain/params.py の dataclass に変換して返す。
"""

from __future__ import annotations

import csv as csv_module
from pathlib import Path
from typing import Any, Dict

import yaml

from ..domain.params import (
    BatteryParams,
    ChassisParams,
    MotorParams,
    RaceRules,
    RollerConfig,
    SectionParams,
    TireParams,
    TrackParams,
    VehicleParams,
)


def load_yaml(path: Path) -> Dict[str, Any]:
    """
    YAML ファイルを読み込んで辞書として返す。

    入力:
        path : YAMLファイルのパス

    出力:
        辞書形式のデータ
    """
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_motor_params(data: Dict[str, Any]) -> MotorParams:
    """
    辞書（インライン YAML 形式）から MotorParams を構築する。

    入力:
        data : motor セクションの辞書

    出力:
        MotorParams
    """
    return MotorParams(
        name=data["name"],
        no_load_rpm=float(data["no_load_rpm"]),
        stall_torque_Nmm=float(data["stall_torque_Nmm"]),
        no_load_current_A=float(data["no_load_current_A"]),
        stall_current_A=float(data["stall_current_A"]),
        rated_voltage_v=float(data["rated_voltage_v"]),
    )


def load_motor_params_from_csv(csv_path: Path, motor_name: str) -> MotorParams:
    """
    Summary.csv からモーター名で1行を検索し MotorParams を構築する。

    入力:
        csv_path   : Summary.csv のパス
        motor_name : 取得するモーター名（MotorName 列に一致する文字列）

    出力:
        MotorParams

    仮定:
        - rated_voltage_v  ← VoltageMax_V
        - no_load_rpm      ← RPM_Max          [仮説: 公式範囲最大を無負荷近似]
        - stall_torque_Nmm ← Torque_Max_mNm   [仮説: 推奨負荷最大を停止トルク近似]
        - no_load_current_A← Current_Min_A
        - stall_current_A  ← Current_Max_A
        CSV の先頭数行にメタ情報行が含まれるため、
        'MotorName' が先頭セルの行を動的にヘッダーとして検出する。

    例外:
        ValueError : motor_name が CSV に見つからない場合
    """
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv_module.reader(f)

        # 'MotorName' が先頭セルの行をヘッダーとして検出する
        header: list[str] | None = None
        for row in reader:
            if row and row[0].strip() == "MotorName":
                header = [col.strip() for col in row]
                break

        if header is None:
            raise ValueError(
                f"{csv_path} に 'MotorName' ヘッダー行が見つかりません"
            )

        for row in reader:
            if not row or not row[0].strip():
                continue
            data = dict(zip(header, [col.strip() for col in row]))
            if data.get("MotorName") == motor_name:
                # 失速トルクは動作範囲データから線形モデルで外挿する
                # 公式 PDF の Torque_Max は動作範囲最大負荷（高負荷端）、
                # RPM_Min は Torque_Max 時の回転数（低速端）。
                # 線形 T-N 特性を RPM=0 まで延長した値が stall_torque:
                #   stall_torque = Torque_Max × RPM_Max / (RPM_Max - RPM_Min)
                rpm_max = float(data["RPM_Max"])
                rpm_min = float(data["RPM_Min"])
                torque_max = float(data["Torque_Max_mNm"])
                if rpm_max > rpm_min:
                    stall_torque_Nmm = torque_max * rpm_max / (rpm_max - rpm_min)
                else:
                    stall_torque_Nmm = torque_max  # フォールバック（データ異常時）
                return MotorParams(
                    name=data["MotorName"],
                    rated_voltage_v=float(data["VoltageMax_V"]),
                    no_load_rpm=rpm_max,
                    stall_torque_Nmm=stall_torque_Nmm,
                    no_load_current_A=float(data["Current_Min_A"]),
                    stall_current_A=float(data["Current_Max_A"]),
                )

    raise ValueError(
        f"モーター名 '{motor_name}' が {csv_path} に見つかりません。"
        f" Summary.csv の MotorName 列を確認してください。"
    )


def load_battery_params(data: Dict[str, Any]) -> BatteryParams:
    """
    辞書から BatteryParams を構築する。

    入力:
        data : battery セクションの辞書

    出力:
        BatteryParams
    """
    discharge_curve = [
        (float(row[0]), float(row[1]))
        for row in data.get("discharge_curve", [])
    ]
    return BatteryParams(
        battery_type=data["battery_type"],
        nominal_voltage_v=float(data["nominal_voltage_v"]),
        capacity_mAh=float(data["capacity_mAh"]),
        internal_resistance_ohm=float(data["internal_resistance_ohm"]),
        discharge_curve=discharge_curve,
    )


def load_tire_params(data: Dict[str, Any]) -> TireParams:
    """
    辞書から TireParams を構築する。

    入力:
        data : tire セクションの辞書

    出力:
        TireParams
    """
    return TireParams(
        name=data.get("name", ""),
        diameter_mm=float(data["diameter_mm"]),
        width_mm=float(data["width_mm"]),
        material=data.get("material", "medium"),
        friction_coef=float(data.get("friction_coef", 0.80)),
        rolling_resistance_coef=float(data.get("rolling_resistance_coef", 0.025)),
        cornering_stiffness_N_per_rad=float(data.get("cornering_stiffness_N_per_rad", 8.0)),
    )


def load_roller_config(data: Dict[str, Any]) -> RollerConfig:
    """
    辞書から RollerConfig を構築する。

    入力:
        data : roller セクションの辞書

    出力:
        RollerConfig
    """
    return RollerConfig(
        front_diameter_mm=float(data["front_diameter_mm"]),
        rear_diameter_mm=float(data["rear_diameter_mm"]),
        front_position_from_axle_mm=float(data.get("front_position_from_axle_mm", 35.0)),
        rear_position_from_axle_mm=float(data.get("rear_position_from_axle_mm", 45.0)),
        track_width_mm=float(data.get("track_width_mm", 105.0)),
        front_friction_coef=float(data.get("front_friction_coef", 0.05)),
        rear_friction_coef=float(data.get("rear_friction_coef", 0.05)),
    )


def load_chassis_params(data: Dict[str, Any]) -> ChassisParams:
    """
    辞書から ChassisParams を構築する。

    入力:
        data : chassis セクションの辞書

    出力:
        ChassisParams
    """
    return ChassisParams(
        chassis_type=data["chassis_type"],
        wheelbase_mm=float(data["wheelbase_mm"]),
        track_width_front_mm=float(data.get("track_width_front_mm", 90.0)),
        track_width_rear_mm=float(data.get("track_width_rear_mm", 92.0)),
        mass_kg=float(data.get("mass_kg", 0.080)),
        com_height_mm=float(data.get("com_height_mm", 15.0)),
    )


def load_vehicle_params(path: Path) -> VehicleParams:
    """
    vehicle_example.yaml（またはその互換ファイル）から VehicleParams を読み込む。

    入力:
        path : 車体設定 YAML ファイルのパス

    出力:
        VehicleParams
    """
    raw = load_yaml(path)
    v = raw["vehicle"]

    # motor セクションが csv キーを持つ場合は CSV から読み込む
    motor_data = raw["motor"]
    if "csv" in motor_data:
        csv_path = (path.parent / motor_data["csv"]).resolve()
        motor = load_motor_params_from_csv(csv_path, motor_data["name"])
    else:
        motor = load_motor_params(motor_data)

    battery = load_battery_params(raw["battery"])

    # tire セクション（省略可: 後方互換）
    tire = load_tire_params(raw["tire"]) if "tire" in raw else None

    # roller セクション（省略可）
    roller = load_roller_config(raw["roller"]) if "roller" in raw else None

    # chassis セクション（省略可）
    chassis = load_chassis_params(raw["chassis"]) if "chassis" in raw else None

    # tire_diameter_mm: tire セクションが優先、なければ vehicle セクション
    if tire is not None:
        tire_diameter = tire.diameter_mm
        rolling_res = tire.rolling_resistance_coef
    else:
        tire_diameter = float(v["tire_diameter_mm"])
        rolling_res = float(v.get("rolling_resistance_coef", 0.025))

    return VehicleParams(
        mass_kg=float(v["mass_kg"]),
        tire_diameter_mm=tire_diameter,
        gear_ratio=float(v["gear_ratio"]),
        drivetrain_type=v["drivetrain_type"],
        motor=motor,
        battery=battery,
        rolling_resistance_coef=rolling_res,
        drivetrain_efficiency=float(v.get("drivetrain_efficiency", 0.85)),
        tire=tire,
        roller=roller,
        chassis=chassis,
    )


def _load_sections_from_csv(
    csv_path: Path,
    column_map: Dict[str, str],
) -> list:
    """
    CSV ファイルからセクションパラメータのリストを読み込む。

    入力:
        csv_path   : セクション定義 CSV ファイルのパス
        column_map : SectionParams フィールド名 → CSV 列名 のマッピング辞書

    出力:
        SectionParams のリスト

    仮定:
        CSV の先頭行はヘッダー行である。
        slope_deg 列が空の場合は 0.0 とみなす。
        note 列が存在しない or 空の場合は "" とみなす。
    """
    with open(csv_path, encoding="utf-8-sig", newline="") as f:
        reader = csv_module.DictReader(f)
        rows = list(reader)

    sections = []
    for row in rows:
        # ヘッダーマッピング（column_map: fields → csv_col）
        def _get(field: str, default: str = "") -> str:
            csv_col = column_map.get(field, field)
            return row.get(csv_col, default).strip()

        slope_raw = _get("slope_deg", "0")
        sections.append(
            SectionParams(
                section_id=int(_get("section_id")),
                section_type=_get("section_type"),
                length_mm=float(_get("length_mm")),
                slope_deg=float(slope_raw) if slope_raw else 0.0,
                note=_get("note", ""),
            )
        )
    return sections


def load_track_params(path: Path) -> TrackParams:
    """
    コース設定 YAML から TrackParams を読み込む。

    セクション定義の2つの記述方式に対応する:

    【CSV 参照方式】（推奨）
        track:
          sections_csv: "../data/course.csv"
          column_map:
            section_id:   "section"
            section_type: "type"
            ...

    【インライン方式】（後方互換）
        track:
          sections:
            - section_id: 1
              section_type: straight
              ...

    入力:
        path : コース設定 YAML ファイルのパス

    出力:
        TrackParams
    """
    raw = load_yaml(path)
    t = raw["track"]

    if "sections_csv" in t:
        # CSV 参照方式
        csv_path = (path.parent / t["sections_csv"]).resolve()
        column_map: Dict[str, str] = t.get("column_map", {})
        sections = _load_sections_from_csv(csv_path, column_map)
    else:
        # インライン方式（後方互換）
        sections = [
            SectionParams(
                section_id=int(s["section_id"]),
                section_type=s["section_type"],
                length_mm=float(s["length_mm"]),
                slope_deg=float(s.get("slope_deg", 0.0)),
                note=s.get("note", ""),
            )
            for s in t["sections"]
        ]

    return TrackParams(
        name=t["name"],
        sections=sections,
        corner_radius_mm=float(t["corner_radius_mm"]),
        obstacle_height_mm=float(t["obstacle_height_mm"]),
        obstacle_per_lap=int(t.get("obstacle_per_lap", 1)),
    )


def load_race_rules(path: Path) -> RaceRules:
    """
    default.yaml（またはその互換ファイル）から RaceRules を読み込む。

    入力:
        path : デフォルト設定 YAML ファイルのパス

    出力:
        RaceRules
    """
    raw = load_yaml(path)
    r = raw["race"]

    return RaceRules(
        time_limit_s=float(r["time_limit_s"]),
        dnf_speed_threshold_mps=float(r.get("dnf_speed_threshold_mps", 0.05)),
    )


def load_physics_config(path: Path) -> Dict[str, Any]:
    """
    default.yaml から physics セクションを辞書として読み込む。

    入力:
        path : デフォルト設定 YAML ファイルのパス

    出力:
        物理係数設定の辞書
    """
    raw = load_yaml(path)
    return raw.get("physics", {})
