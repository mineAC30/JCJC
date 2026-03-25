"""
タイヤモデル

スリップ角・横力・ローラー側面力を計算する。

【物理モデル概要】
    コーナーでは車体を円弧に沿わせるために横力が必要。
        F_lat_required = m × v² / r  [遠心力 = 必要横力]

    タイヤが発生できる最大横力:
        F_lat_max = μ × m × g  [摩擦円近似、平坦路]

    タイヤスリップ角（線形タイヤモデル）:
        α = F_lat_required / C_α  [rad]
        ここで C_α はコーナリングスティフネス [N/rad]

    タイヤ横力限界を超えた分はローラーがガイドレールから支持:
        F_roller = max(0, F_lat_required - F_lat_max)

    ローラー接触による走行方向への抵抗:
        F_drag = F_roller × μ_roller_avg

【仮定】
    - 線形タイヤモデル（小スリップ角域）[仮説値]
    - コーナリングスティフネス C_α は定数（速度・荷重依存性を無視） [仮説値]
    - 法線力 = m × g（平坦路近似。傾斜補正なし） [仮説値]
    - フロント・リアローラーの平均摩擦係数を使用 [仮説値]
"""

from __future__ import annotations

import math

from ..domain.params import RollerConfig, TireParams

_GRAVITY_MPS2 = 9.81  # 重力加速度 [m/s²]


def compute_lateral_force_required_N(
    mass_kg: float,
    speed_mps: float,
    corner_radius_mm: float,
) -> float:
    """
    コーナー走行に必要な横力（遠心力）を計算する。

    入力:
        mass_kg          : 車体質量 [kg]
        speed_mps        : 走行速度 [m/s]
        corner_radius_mm : コーナー半径 [mm]

    出力:
        必要横力 [N]

    仮定:
        F_lat = m × v² / r
    """
    r_m = corner_radius_mm / 1000.0
    if r_m <= 0:
        return 0.0
    return mass_kg * speed_mps ** 2 / r_m


def compute_tire_lateral_capacity_N(
    mass_kg: float,
    tire: TireParams,
) -> float:
    """
    タイヤが発生できる最大横力を計算する。

    入力:
        mass_kg : 車体質量 [kg]
        tire    : タイヤパラメータ

    出力:
        最大横力 [N]

    仮定:
        F_lat_max = μ × m × g（法線力 = m × g で平坦路近似）
    """
    return tire.friction_coef * mass_kg * _GRAVITY_MPS2


def compute_slip_angle_rad(
    mass_kg: float,
    speed_mps: float,
    corner_radius_mm: float,
    cornering_stiffness_N_per_rad: float,
) -> float:
    """
    タイヤスリップ角を計算する。

    入力:
        mass_kg                      : 車体質量 [kg]
        speed_mps                    : 走行速度 [m/s]
        corner_radius_mm             : コーナー半径 [mm]
        cornering_stiffness_N_per_rad: コーナリングスティフネス [N/rad]

    出力:
        スリップ角 [rad]

    仮定:
        線形タイヤモデル: F_lat = C_α × α  →  α = F_lat / C_α
        F_lat = m × v² / r（遠心力 = 必要横力）
        正値はアンダーステア方向。
    """
    if cornering_stiffness_N_per_rad <= 0:
        return 0.0
    F_lat = compute_lateral_force_required_N(mass_kg, speed_mps, corner_radius_mm)
    return F_lat / cornering_stiffness_N_per_rad


def compute_roller_side_force_N(
    mass_kg: float,
    speed_mps: float,
    corner_radius_mm: float,
    tire: TireParams,
) -> float:
    """
    ローラーがコースガイドから受ける横力を計算する。

    入力:
        mass_kg          : 車体質量 [kg]
        speed_mps        : 走行速度 [m/s]
        corner_radius_mm : コーナー半径 [mm]
        tire             : タイヤパラメータ

    出力:
        ローラー側面力 [N]（0以上）

    仮定:
        タイヤが横力上限まで負担し、残りをローラーが支持する。
        F_roller = max(0, F_centripetal - F_tire_max)
    """
    F_required = compute_lateral_force_required_N(mass_kg, speed_mps, corner_radius_mm)
    F_tire_max = compute_tire_lateral_capacity_N(mass_kg, tire)
    return max(0.0, F_required - F_tire_max)


def compute_roller_friction_drag_N(
    roller_side_force_N: float,
    roller: RollerConfig,
) -> float:
    """
    ローラー側面接触による走行方向への摩擦抵抗力を計算する。

    入力:
        roller_side_force_N : ローラー側面力 [N]
        roller              : ローラー配置パラメータ

    出力:
        ローラー摩擦抵抗力 [N]

    仮定:
        フロント・リアの平均摩擦係数を使用する。
        F_drag = F_roller × μ_avg
    """
    avg_friction_coef = (roller.front_friction_coef + roller.rear_friction_coef) / 2.0
    return roller_side_force_N * avg_friction_coef


def compute_corner_equilibrium_speed_mps(
    mass_kg: float,
    v_noload_mps: float,
    stall_force_wheel_N: float,
    base_resistance_N: float,
    corner_radius_mm: float,
    tire: TireParams,
    roller: RollerConfig,
) -> float:
    """
    コーナー区間でのタイヤ＋ローラーモデルにおける均衡速度を解析的に計算する。

    【物理モデル】
    線形モータモデル:
        F_drive(v) = F_stall × (1 − v / v_noload)

    コーナー走行抵抗（ローラー係合域 v > v_crit）:
        F_resist(v) = F_base + max(0, m×v²/r − μ_tire×m×g) × μ_roller

    균衡条件 F_drive(v) = F_resist(v) を整理すると二次方程式:
        D×v² + A×v − (B − C) = 0
        D = m × μ_roller / r
        A = F_stall / v_noload
        B = F_stall
        C = F_base − μ_tire × m × g × μ_roller

    入力:
        mass_kg              : 車体質量 [kg]
        v_noload_mps         : モーター無負荷速度（現在電圧換算） [m/s]
        stall_force_wheel_N  : タイヤ接地点でのモーター最大推力 [N]（現在電圧換算）
        base_resistance_N    : 転がり抵抗＋勾配方向力 [N]
        corner_radius_mm     : コーナー半径 [mm]
        tire                 : タイヤパラメータ
        roller               : ローラーパラメータ

    出力:
        均衡コーナー速度 [m/s]（ローラーが係合しない場合はローラーなし均衡速度）

    仮定:
        - 線形タイヤ＆モーターモデルを前提
        - 方程式の正の実数解を採用
    """
    if v_noload_mps <= 0 or stall_force_wheel_N <= 0:
        return 0.0

    r_m = corner_radius_mm / 1000.0
    mu_tire = tire.friction_coef
    mu_roller = (roller.front_friction_coef + roller.rear_friction_coef) / 2.0

    # ローラーなしの均衡速度（直線と同じ計算）
    v_no_roller = v_noload_mps * (1.0 - base_resistance_N / stall_force_wheel_N)
    if v_no_roller <= 0:
        return 0.0

    # ローラー係合閾値速度: v_crit² = μ_tire × g × r
    v_crit_sq = mu_tire * _GRAVITY_MPS2 * r_m

    if v_no_roller ** 2 <= v_crit_sq:
        # ローラー係合なし（タイヤ摩擦だけで遠心力を負担できる低速域）
        return v_no_roller

    # ローラー係合域の二次方程式を解く:
    #   D×v² + A×v − (B − C) = 0
    D = mass_kg * mu_roller / r_m
    A = stall_force_wheel_N / v_noload_mps
    B = stall_force_wheel_N
    C = base_resistance_N - mu_tire * mass_kg * _GRAVITY_MPS2 * mu_roller

    discriminant = A ** 2 + 4.0 * D * (B - C)
    if discriminant < 0:
        return 0.0

    v_sol = (-A + math.sqrt(discriminant)) / (2.0 * D)
    return max(0.0, v_sol)
