"""
モーターモデルのテスト
"""

import pytest

from sim_core.domain.params import MotorParams
from sim_core.physics.motor import compute_motor_current_A, compute_motor_speed_rpm


def _make_motor() -> MotorParams:
    return MotorParams(
        name="test_motor",
        no_load_rpm=15750.0,
        stall_torque_Nmm=7.0,
        no_load_current_A=0.5,
        stall_current_A=5.0,
        rated_voltage_v=3.0,
    )


class TestMotorSpeed:
    def test_no_load_speed_at_rated_voltage(self):
        """無負荷・定格電圧では no_load_rpm が返る"""
        params = _make_motor()
        rpm = compute_motor_speed_rpm(params, voltage_v=3.0, load_torque_Nmm=0.0)
        assert abs(rpm - 15750.0) < 1.0

    def test_stall_condition(self):
        """停止トルクと同等の負荷では回転数ゼロになる"""
        params = _make_motor()
        rpm = compute_motor_speed_rpm(params, voltage_v=3.0, load_torque_Nmm=7.0)
        assert rpm == pytest.approx(0.0, abs=1e-6)

    def test_half_torque_gives_half_no_load_speed(self):
        """線形モデル: トルク = stall/2 のとき rpm = no_load/2"""
        params = _make_motor()
        rpm = compute_motor_speed_rpm(params, voltage_v=3.0, load_torque_Nmm=3.5)
        assert rpm == pytest.approx(15750.0 / 2.0, abs=1.0)

    def test_voltage_scaling(self):
        """電圧を半分にすると回転数も半分になる（線形モデル）"""
        params = _make_motor()
        rpm_full = compute_motor_speed_rpm(params, voltage_v=3.0, load_torque_Nmm=0.0)
        rpm_half = compute_motor_speed_rpm(params, voltage_v=1.5, load_torque_Nmm=0.0)
        assert rpm_half == pytest.approx(rpm_full / 2.0, rel=1e-3)

    def test_zero_voltage_returns_zero(self):
        """電圧ゼロでは回転数ゼロ"""
        params = _make_motor()
        rpm = compute_motor_speed_rpm(params, voltage_v=0.0, load_torque_Nmm=0.0)
        assert rpm == pytest.approx(0.0, abs=1e-6)

    def test_speed_is_non_negative(self):
        """回転数は常に非負"""
        params = _make_motor()
        rpm = compute_motor_speed_rpm(params, voltage_v=3.0, load_torque_Nmm=100.0)
        assert rpm >= 0.0


class TestMotorCurrent:
    def test_no_load_current_at_rated_voltage(self):
        """無負荷・定格電圧では no_load_current_A が返る"""
        params = _make_motor()
        current = compute_motor_current_A(params, voltage_v=3.0, load_torque_Nmm=0.0)
        assert current == pytest.approx(0.5, rel=1e-3)

    def test_stall_current_at_rated_voltage(self):
        """停止負荷では stall_current_A が返る"""
        params = _make_motor()
        current = compute_motor_current_A(params, voltage_v=3.0, load_torque_Nmm=7.0)
        assert current == pytest.approx(5.0, rel=1e-3)

    def test_current_between_bounds(self):
        """中間トルクでは電流が no_load と stall の間に入る"""
        params = _make_motor()
        current = compute_motor_current_A(params, voltage_v=3.0, load_torque_Nmm=3.5)
        assert params.no_load_current_A < current < params.stall_current_A

    def test_current_is_non_negative(self):
        """電流は常に非負"""
        params = _make_motor()
        current = compute_motor_current_A(params, voltage_v=0.0, load_torque_Nmm=0.0)
        assert current >= 0.0
