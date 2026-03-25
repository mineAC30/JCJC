"""
モーターモデル（線形近似）

仮定:
    - 直流整流子モーターの線形トルク-回転数特性を使用する
    - 電圧に対して回転数・トルクは比例スケーリングする
    - 鉄損・温度変化は無視する（簡易モデル）

参考式:
    定格電圧 V0 での特性をベースに、電圧 V での特性を以下でスケーリング:
        no_load_rpm(V) = no_load_rpm(V0) * (V / V0)
        stall_torque(V) = stall_torque(V0) * (V / V0)
    
    トルク-回転数の線形特性:
        rpm(T) = no_load_rpm(V) * (1 - T / stall_torque(V))
    
    電流-トルクの線形特性（近似）:
        I(T) = I_stall * (T / stall_torque(V)) + I_no_load * (1 - T / stall_torque(V))
"""

from ..domain.params import MotorParams


def compute_motor_speed_rpm(
    params: MotorParams,
    voltage_v: float,
    load_torque_Nmm: float,
) -> float:
    """
    与えられた電圧・負荷トルクからモーター回転数を計算する。

    入力:
        params          : モーターパラメータ
        voltage_v       : 端子電圧 [V]
        load_torque_Nmm : 負荷トルク [N·mm]（0 = 無負荷）

    出力:
        回転数 [rpm]（負にはならない）

    仮定:
        線形モデル。実際のモーター特性とは一致しない場合がある。
    """
    voltage_ratio = voltage_v / params.rated_voltage_v
    no_load_rpm = params.no_load_rpm * voltage_ratio
    stall_torque = params.stall_torque_Nmm * voltage_ratio

    if stall_torque <= 0.0:
        return 0.0

    torque_ratio = min(load_torque_Nmm / stall_torque, 1.0)
    rpm = no_load_rpm * (1.0 - torque_ratio)
    return max(rpm, 0.0)


def compute_motor_current_A(
    params: MotorParams,
    voltage_v: float,
    load_torque_Nmm: float,
) -> float:
    """
    与えられた電圧・負荷トルクからモーター電流を計算する。

    入力:
        params          : モーターパラメータ
        voltage_v       : 端子電圧 [V]
        load_torque_Nmm : 負荷トルク [N·mm]

    出力:
        電流 [A]（負にはならない）

    仮定:
        電流はトルク比に対して線形補間する（無負荷電流 〜 停止電流）。
    """
    voltage_ratio = voltage_v / params.rated_voltage_v
    stall_torque = params.stall_torque_Nmm * voltage_ratio

    if stall_torque <= 0.0:
        return 0.0

    torque_ratio = min(load_torque_Nmm / stall_torque, 1.0)
    current = (
        params.stall_current_A * voltage_ratio * torque_ratio
        + params.no_load_current_A * voltage_ratio * (1.0 - torque_ratio)
    )
    return max(current, 0.0)
