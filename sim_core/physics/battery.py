"""
電池モデル

仮定:
    - 内部抵抗は一定（温度・劣化変動を無視）
    - 端子電圧 = 開路電圧 - 電流 × 内部抵抗
    - 放電曲線は SOC に対して線形補間する
    - 容量は電流×時間の積算で減少する（クーロンカウント）
"""

from typing import List, Tuple

from ..domain.params import BatteryParams
from ..domain.state import BatteryState


def initialize_battery(params: BatteryParams) -> BatteryState:
    """
    電池の初期状態（フル充電）を生成する。

    入力:
        params : 電池パラメータ

    出力:
        BatteryState（SOC=1.0、フル充電）
    """
    return BatteryState(
        voltage_v=get_open_circuit_voltage(params, 1.0),
        charge_remaining_mAh=params.capacity_mAh,
        soc=1.0,
        total_consumed_mAh=0.0,
    )


def get_open_circuit_voltage(params: BatteryParams, soc: float) -> float:
    """
    SOC から開路電圧を計算する（放電曲線の線形補間）。

    入力:
        params : 電池パラメータ
        soc    : State of Charge [0-1]

    出力:
        開路電圧 [V]

    仮定:
        放電曲線が未設定の場合、nominal_voltage_v を基準に線形減衰する。
    """
    if not params.discharge_curve:
        # フォールバック: 公称電圧の 80〜100% で線形
        return params.nominal_voltage_v * (0.80 + 0.20 * soc)

    curve: List[Tuple[float, float]] = sorted(params.discharge_curve, key=lambda x: x[0])

    if soc <= curve[0][0]:
        return curve[0][1]
    if soc >= curve[-1][0]:
        return curve[-1][1]

    for i in range(len(curve) - 1):
        s0, v0 = curve[i]
        s1, v1 = curve[i + 1]
        if s0 <= soc <= s1:
            t = (soc - s0) / (s1 - s0)
            return v0 + t * (v1 - v0)

    return params.nominal_voltage_v  # ここには到達しないが保険


def compute_terminal_voltage(
    params: BatteryParams,
    state: BatteryState,
    current_A: float,
) -> float:
    """
    負荷電流から端子電圧を計算する。

    入力:
        params    : 電池パラメータ
        state     : 電池の現在状態
        current_A : 負荷電流 [A]

    出力:
        端子電圧 [V]（0V 未満にはならない）

    仮定:
        V_terminal = V_ocv - I × R_internal
    """
    ocv = get_open_circuit_voltage(params, state.soc)
    terminal_v = ocv - current_A * params.internal_resistance_ohm
    return max(terminal_v, 0.0)


def discharge_battery(
    params: BatteryParams,
    state: BatteryState,
    current_A: float,
    time_s: float,
) -> BatteryState:
    """
    指定の電流・時間で電池を放電し、新しい状態を返す（イミュータブル）。

    入力:
        params    : 電池パラメータ
        state     : 電池の現在状態
        current_A : 放電電流 [A]
        time_s    : 放電時間 [s]

    出力:
        更新された BatteryState
    """
    consumed_mAh = current_A * (time_s / 3600.0) * 1000.0
    new_remaining = max(state.charge_remaining_mAh - consumed_mAh, 0.0)
    new_soc = new_remaining / params.capacity_mAh if params.capacity_mAh > 0 else 0.0
    new_ocv = get_open_circuit_voltage(params, new_soc)

    return BatteryState(
        voltage_v=new_ocv,
        charge_remaining_mAh=new_remaining,
        soc=new_soc,
        total_consumed_mAh=state.total_consumed_mAh + consumed_mAh,
    )
