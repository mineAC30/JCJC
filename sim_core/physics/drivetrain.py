"""
駆動系モデル

モーター回転数 → タイヤ回転数 → 車体速度 の変換、
および 走行抵抗力 → タイヤトルク → モータートルク の逆変換。

仮定:
    - ギア比・駆動効率は一定
    - タイヤはスリップなしで回転する（純転がり）
"""

import math

from ..domain.params import VehicleParams


def compute_wheel_speed_mps(
    params: VehicleParams,
    motor_rpm: float,
) -> float:
    """
    モーター回転数から車体速度を計算する。

    入力:
        params    : 車体パラメータ
        motor_rpm : モーター回転数 [rpm]

    出力:
        車体速度 [m/s]
    """
    tire_radius_m = (params.tire_diameter_mm / 2.0) / 1000.0
    wheel_rpm = motor_rpm / params.gear_ratio
    speed_mps = wheel_rpm * 2.0 * math.pi * tire_radius_m / 60.0
    return max(speed_mps, 0.0)


def compute_required_motor_torque_Nmm(
    params: VehicleParams,
    resistance_force_N: float,
) -> float:
    """
    走行抵抗力から必要なモータートルクを計算する。

    入力:
        params              : 車体パラメータ
        resistance_force_N  : 走行方向の合計抵抗力 [N]（摩擦+重力成分）

    出力:
        必要なモータートルク [N·mm]

    仮定:
        motor_torque = wheel_torque / (gear_ratio × efficiency)
        wheel_torque = force × tire_radius
    """
    tire_radius_mm = params.tire_diameter_mm / 2.0
    wheel_torque_Nmm = resistance_force_N * tire_radius_mm
    motor_torque_Nmm = wheel_torque_Nmm / (
        params.gear_ratio * params.drivetrain_efficiency
    )
    return max(motor_torque_Nmm, 0.0)
