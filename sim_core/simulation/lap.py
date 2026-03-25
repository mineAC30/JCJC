"""
1周シミュレーションモジュール

【アルゴリズム概要】
    1. コースの各区間を順に処理する
    2. 各区間では「定常走行速度」を計算する（加速・減速の過渡は無視）
    3. 区間タイプに応じて速度制限を適用する
       - curve       : コーナー最大速度で制限
       - lane_change : 速度低下係数を適用
       - slope_up/down: 傾斜成分が抵抗力・推進力として自動反映
    4. 各区間の通過時間とエネルギー消費を算出し電池状態を更新する
    5. 1周終了時に段差（ゴム障害物）の速度低下を適用する

【仮定】
    - 各区間は定常状態で走行する（過渡応答は捨象）
    - 電池電圧は区間内で一定と近似する
    - 段差は1周に1回、最終区間通過後に適用する
"""

from __future__ import annotations

from typing import Dict, Tuple

from ..domain.params import RaceRules, SectionParams, TrackParams, VehicleParams
from ..domain.results import LapResult, SectionResult
from ..domain.state import BatteryState
from ..physics import battery as battery_physics
from ..physics import corner as corner_physics
from ..physics import drivetrain as drivetrain_physics
from ..physics import motor as motor_physics
from ..physics import obstacle as obstacle_physics
from ..physics import resistance as resistance_physics
from ..physics import tire as tire_physics


def _compute_steady_state_speed(
    section: SectionParams,
    vehicle_params: VehicleParams,
    track_params: TrackParams,
    battery_state: BatteryState,
    physics_config: Dict,
    extra_resistance_N: float = 0.0,
) -> Tuple[float, float]:
    """
    区間の定常走行速度と消費電流を計算する。

    入力:
        section            : 区間パラメータ
        vehicle_params     : 車体パラメータ
        track_params       : コースパラメータ
        battery_state      : 現在の電池状態
        physics_config     : 物理係数設定（コーナー摩擦係数等）
        extra_resistance_N : 追加抵抗力 [N]（ローラー摩擦ドラグ等） デフォルト 0

    出力:
        (speed_mps, current_A)
        - speed_mps  : 定常走行速度 [m/s]（コーナー制限前）
        - current_A  : 対応するモーター電流 [A]

    仮定:
        1回の線形計算（フィードバックなし簡易版）。
        端子電圧の計算に今のSOCの開路電圧を利用する。
    """
    # 走行抵抗力を計算
    roll_force_N = resistance_physics.compute_rolling_resistance_N(
        vehicle_params.mass_kg,
        vehicle_params.rolling_resistance_coef,
        section.slope_deg,
    )
    grav_force_N = resistance_physics.compute_gravity_component_N(
        vehicle_params.mass_kg,
        section.slope_deg,
    )
    total_resistance_N = roll_force_N + grav_force_N + extra_resistance_N

    # 必要モータートルクを計算
    required_torque_Nmm = drivetrain_physics.compute_required_motor_torque_Nmm(
        vehicle_params, total_resistance_N
    )

    # 電流を概算し端子電圧を決定
    current_A = motor_physics.compute_motor_current_A(
        vehicle_params.motor,
        battery_state.voltage_v,
        required_torque_Nmm,
    )
    terminal_v = battery_physics.compute_terminal_voltage(
        vehicle_params.battery, battery_state, current_A
    )

    # モーター回転数 → 車体速度
    rpm = motor_physics.compute_motor_speed_rpm(
        vehicle_params.motor, terminal_v, required_torque_Nmm
    )
    speed_mps = drivetrain_physics.compute_wheel_speed_mps(vehicle_params, rpm)

    return speed_mps, current_A


def simulate_section(
    section: SectionParams,
    vehicle_params: VehicleParams,
    track_params: TrackParams,
    battery_state: BatteryState,
    incoming_speed_mps: float,
    physics_config: Dict,
) -> Tuple[SectionResult, BatteryState, float]:
    """
    1区間を走行し、結果と更新後の状態を返す。

    入力:
        section           : 区間パラメータ
        vehicle_params    : 車体パラメータ
        track_params      : コースパラメータ
        battery_state     : 走行前の電池状態
        incoming_speed_mps: 区間進入速度 [m/s]
        physics_config    : 物理係数設定

    出力:
        (SectionResult, 更新後 BatteryState, 退出速度 [m/s])
    """
    steady_speed_mps, current_A = _compute_steady_state_speed(
        section, vehicle_params, track_params, battery_state, physics_config
    )

    # 区間タイプによる速度制約を適用
    exit_speed_mps = steady_speed_mps
    speed_loss_mps = 0.0
    slip_angle_rad = 0.0
    roller_side_force_N = 0.0

    if section.section_type == "curve":
        if vehicle_params.tire is not None and vehicle_params.roller is not None:
            # ===== タイヤ + ローラーモデル =====
            # モーター駆動力 = 転がり抵抗 + ローラー摩擦 の均衡方程式を解析的に解く。
            # F_drive(v) = F_stall × (1 - v/v_noload) が二次方程式を形成する。
            v_ratio = battery_state.voltage_v / vehicle_params.motor.rated_voltage_v
            tire_radius_mm = vehicle_params.tire_diameter_mm / 2.0
            v_noload = drivetrain_physics.compute_wheel_speed_mps(
                vehicle_params,
                vehicle_params.motor.no_load_rpm * v_ratio,
            )
            stall_force_wheel_N = (
                vehicle_params.motor.stall_torque_Nmm
                * v_ratio
                * vehicle_params.gear_ratio
                * vehicle_params.drivetrain_efficiency
                / tire_radius_mm
            )
            base_resist_N = (
                resistance_physics.compute_rolling_resistance_N(
                    vehicle_params.mass_kg,
                    vehicle_params.rolling_resistance_coef,
                    section.slope_deg,
                )
                + resistance_physics.compute_gravity_component_N(
                    vehicle_params.mass_kg, section.slope_deg
                )
            )

            # コーナー均衡速度を解析的に求める
            exit_speed_mps = tire_physics.compute_corner_equilibrium_speed_mps(
                vehicle_params.mass_kg,
                v_noload,
                stall_force_wheel_N,
                base_resist_N,
                track_params.corner_radius_mm,
                vehicle_params.tire,
                vehicle_params.roller,
            )

            # 均衡速度でのローラー側面力・スリップ角
            slip_angle_rad = tire_physics.compute_slip_angle_rad(
                vehicle_params.mass_kg,
                exit_speed_mps,
                track_params.corner_radius_mm,
                vehicle_params.tire.cornering_stiffness_N_per_rad,
            )
            roller_side_force_N = tire_physics.compute_roller_side_force_N(
                vehicle_params.mass_kg,
                exit_speed_mps,
                track_params.corner_radius_mm,
                vehicle_params.tire,
            )
            roller_drag_N = tire_physics.compute_roller_friction_drag_N(
                roller_side_force_N, vehicle_params.roller
            )
            speed_loss_mps = max(0.0, steady_speed_mps - exit_speed_mps)

            # エネルギー計算用電流: 均衡速度でのローラー抵抗込み
            _, current_A = _compute_steady_state_speed(
                section, vehicle_params, track_params, battery_state,
                physics_config, extra_resistance_N=roller_drag_N,
            )

        elif vehicle_params.tire is not None:
            # ===== タイヤのみ（ローラーなし）=====
            # タイヤ横力限界で速度上限を設定。
            v_max = corner_physics.compute_max_corner_speed_mps(
                track_params.corner_radius_mm,
                vehicle_params.tire.friction_coef,
            )
            if steady_speed_mps > v_max:
                speed_loss_mps = steady_speed_mps - v_max
                exit_speed_mps = v_max
            slip_angle_rad = tire_physics.compute_slip_angle_rad(
                vehicle_params.mass_kg,
                exit_speed_mps,
                track_params.corner_radius_mm,
                vehicle_params.tire.cornering_stiffness_N_per_rad,
            )

        else:
            # ===== 後方互換モード（TireParams なし）=====
            v_max = corner_physics.compute_max_corner_speed_mps(
                track_params.corner_radius_mm,
                physics_config.get("corner_friction_coefficient", 0.80),
            )
            if steady_speed_mps > v_max:
                speed_loss_mps = steady_speed_mps - v_max
                exit_speed_mps = v_max

    elif section.section_type == "lane_change":
        factor = physics_config.get("lane_change_speed_factor", 0.85)
        exit_speed_mps = steady_speed_mps * factor
        speed_loss_mps = steady_speed_mps * (1.0 - factor)

    # 有効走行速度: 進入速度と退出速度の平均で近似
    effective_speed_mps = (incoming_speed_mps + exit_speed_mps) / 2.0
    effective_speed_mps = max(effective_speed_mps, 1e-6)

    # 区間通過時間を計算
    time_s = section.length_m / effective_speed_mps

    # エネルギー消費を計算
    energy_mAh = current_A * (time_s / 3600.0) * 1000.0

    # 電池状態を更新
    new_battery_state = battery_physics.discharge_battery(
        vehicle_params.battery, battery_state, current_A, time_s
    )

    section_result = SectionResult(
        section_id=section.section_id,
        section_type=section.section_type,
        time_s=time_s,
        energy_consumed_mAh=energy_mAh,
        avg_speed_mps=effective_speed_mps,
        speed_loss_mps=speed_loss_mps,
        slip_angle_rad=slip_angle_rad,
        roller_side_force_N=roller_side_force_N,
    )

    return section_result, new_battery_state, exit_speed_mps


def simulate_lap(
    vehicle_params: VehicleParams,
    track_params: TrackParams,
    battery_state: BatteryState,
    lap_number: int,
    physics_config: Dict,
    race_rules: RaceRules,
) -> Tuple[LapResult, BatteryState]:
    """
    1周のシミュレーションを行う。

    入力:
        vehicle_params : 車体パラメータ
        track_params   : コースパラメータ
        battery_state  : 走行前の電池状態
        lap_number     : 周回番号（1始まり）
        physics_config : 物理係数設定
        race_rules     : レースレギュレーション（DNF判定用）

    出力:
        (LapResult, 走行後の BatteryState)

    仮定:
        - 1周の初速度を、開路電圧に基づく無負荷速度の 70% と推定する
        - 段差による速度低下は最終区間通過後に適用する
    """
    section_results = []
    current_battery = battery_state

    # 初速度の推定
    ocv = battery_physics.get_open_circuit_voltage(
        vehicle_params.battery, battery_state.soc
    )
    no_load_speed_mps = drivetrain_physics.compute_wheel_speed_mps(
        vehicle_params,
        vehicle_params.motor.no_load_rpm * (ocv / vehicle_params.motor.rated_voltage_v),
    )
    current_speed_mps = no_load_speed_mps * 0.70

    for section in track_params.sections:
        section_result, current_battery, current_speed_mps = simulate_section(
            section=section,
            vehicle_params=vehicle_params,
            track_params=track_params,
            battery_state=current_battery,
            incoming_speed_mps=current_speed_mps,
            physics_config=physics_config,
        )
        section_results.append(section_result)

        # 区間通過後に速度不足チェック（途中 DNF の検出）
        if current_speed_mps < race_rules.dnf_speed_threshold_mps:
            total_time_s = sum(sr.time_s for sr in section_results)
            total_energy_mAh = sum(sr.energy_consumed_mAh for sr in section_results)
            lap_result = LapResult(
                lap_number=lap_number,
                time_s=total_time_s,
                energy_consumed_mAh=total_energy_mAh,
                avg_speed_mps=current_speed_mps,
                section_results=section_results,
            )
            return lap_result, current_battery

    # 段差通過（1周に1回、最終区間後）
    for _ in range(track_params.obstacle_per_lap):
        speed_loss = obstacle_physics.compute_obstacle_speed_loss_mps(
            track_params.obstacle_height_mm,
            current_speed_mps,
            physics_config.get("obstacle_loss_coefficient", 0.15),
        )
        current_speed_mps = max(current_speed_mps - speed_loss, 0.0)

    # 周回集計
    total_time_s = sum(sr.time_s for sr in section_results)
    total_energy_mAh = sum(sr.energy_consumed_mAh for sr in section_results)
    avg_speed_mps = (
        track_params.lap_length_m / total_time_s if total_time_s > 0 else 0.0
    )

    lap_result = LapResult(
        lap_number=lap_number,
        time_s=total_time_s,
        energy_consumed_mAh=total_energy_mAh,
        avg_speed_mps=avg_speed_mps,
        section_results=section_results,
    )

    return lap_result, current_battery
