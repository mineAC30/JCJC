"""
電池モデルのテスト
"""

import pytest

from sim_core.domain.params import BatteryParams
from sim_core.physics.battery import (
    compute_terminal_voltage,
    discharge_battery,
    get_open_circuit_voltage,
    initialize_battery,
)

_DISCHARGE_CURVE = [
    (1.0, 2.72),
    (0.8, 2.65),
    (0.6, 2.58),
    (0.4, 2.52),
    (0.2, 2.45),
    (0.0, 2.20),
]


def _make_battery() -> BatteryParams:
    return BatteryParams(
        battery_type="NiMH",
        nominal_voltage_v=2.72,
        capacity_mAh=2400.0,
        internal_resistance_ohm=0.05,
        discharge_curve=_DISCHARGE_CURVE,
    )


class TestInitializeBattery:
    def test_initial_soc_is_one(self):
        state = initialize_battery(_make_battery())
        assert state.soc == pytest.approx(1.0)

    def test_initial_remaining_equals_capacity(self):
        params = _make_battery()
        state = initialize_battery(params)
        assert state.charge_remaining_mAh == pytest.approx(params.capacity_mAh)

    def test_initial_consumed_is_zero(self):
        state = initialize_battery(_make_battery())
        assert state.total_consumed_mAh == pytest.approx(0.0)


class TestOpenCircuitVoltage:
    def test_full_charge_voltage(self):
        """SOC=1.0 では放電曲線の最大電圧が返る"""
        params = _make_battery()
        v = get_open_circuit_voltage(params, soc=1.0)
        assert v == pytest.approx(2.72)

    def test_empty_charge_voltage(self):
        """SOC=0.0 では放電曲線の最小電圧が返る"""
        params = _make_battery()
        v = get_open_circuit_voltage(params, soc=0.0)
        assert v == pytest.approx(2.20)

    def test_interpolation_at_midpoint(self):
        """SOC=0.9 は (1.0, 2.72) と (0.8, 2.65) の中間値になる"""
        params = _make_battery()
        v = get_open_circuit_voltage(params, soc=0.9)
        assert v == pytest.approx((2.72 + 2.65) / 2.0, abs=1e-6)

    def test_voltage_decreases_with_soc(self):
        """電圧はSOCが下がるにつれ単調減少する"""
        params = _make_battery()
        socs = [1.0, 0.8, 0.6, 0.4, 0.2, 0.0]
        voltages = [get_open_circuit_voltage(params, s) for s in socs]
        assert voltages == sorted(voltages, reverse=True)


class TestTerminalVoltage:
    def test_no_current_equals_ocv(self):
        """電流ゼロでは端子電圧 = 開路電圧"""
        params = _make_battery()
        state = initialize_battery(params)
        terminal_v = compute_terminal_voltage(params, state, current_A=0.0)
        ocv = get_open_circuit_voltage(params, state.soc)
        assert terminal_v == pytest.approx(ocv)

    def test_voltage_drop_under_load(self):
        """電流あり: V_terminal = V_ocv - I × R"""
        params = _make_battery()
        state = initialize_battery(params)
        current_A = 2.0
        expected = get_open_circuit_voltage(params, 1.0) - current_A * params.internal_resistance_ohm
        terminal_v = compute_terminal_voltage(params, state, current_A=current_A)
        assert terminal_v == pytest.approx(expected)

    def test_terminal_voltage_is_non_negative(self):
        """端子電圧は常に非負"""
        params = _make_battery()
        state = initialize_battery(params)
        terminal_v = compute_terminal_voltage(params, state, current_A=1000.0)
        assert terminal_v >= 0.0


class TestDischargeBattery:
    def test_consumed_energy_accumulates(self):
        """消費量が正しく積算される"""
        params = _make_battery()
        state = initialize_battery(params)
        # 1A × 3600s = 1Ah = 1000mAh
        new_state = discharge_battery(params, state, current_A=1.0, time_s=3600.0)
        assert new_state.total_consumed_mAh == pytest.approx(1000.0)

    def test_remaining_decreases(self):
        """残量が減少する"""
        params = _make_battery()
        state = initialize_battery(params)
        new_state = discharge_battery(params, state, current_A=1.0, time_s=3600.0)
        assert new_state.charge_remaining_mAh < state.charge_remaining_mAh

    def test_soc_decreases(self):
        """SOC が減少する"""
        params = _make_battery()
        state = initialize_battery(params)
        new_state = discharge_battery(params, state, current_A=1.0, time_s=3600.0)
        assert new_state.soc < state.soc

    def test_remaining_is_non_negative(self):
        """残量は非負（過放電しない）"""
        params = _make_battery()
        state = initialize_battery(params)
        new_state = discharge_battery(params, state, current_A=100.0, time_s=3600.0)
        assert new_state.charge_remaining_mAh >= 0.0
