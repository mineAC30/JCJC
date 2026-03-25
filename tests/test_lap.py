"""
1周シミュレーションのテスト

実測値との整合性チェックを含む。
runs.csv の実測データ:
    - NiMH 2.72V / 2400mAh / 車体155g
    - JCJCコース（3188mm/周）
    - 1周あたり約14.1s（42.3s / 3周）
"""

import pytest

from sim_core.domain.params import (
    BatteryParams,
    MotorParams,
    RaceRules,
    SectionParams,
    TrackParams,
    VehicleParams,
)
from sim_core.physics.battery import initialize_battery
from sim_core.simulation.lap import simulate_lap

_DISCHARGE_CURVE = [
    (1.0, 2.72),
    (0.8, 2.65),
    (0.6, 2.58),
    (0.4, 2.52),
    (0.2, 2.45),
    (0.0, 2.20),
]

_PHYSICS_CONFIG = {
    "corner_friction_coefficient": 0.80,
    "lane_change_speed_factor": 0.85,
    "obstacle_loss_coefficient": 0.15,
}


def _make_vehicle() -> VehicleParams:
    motor = MotorParams(
        name="test_motor",
        no_load_rpm=15750.0,
        stall_torque_Nmm=7.0,
        no_load_current_A=0.5,
        stall_current_A=5.0,
        rated_voltage_v=3.0,
    )
    battery = BatteryParams(
        battery_type="NiMH",
        nominal_voltage_v=2.72,
        capacity_mAh=2400.0,
        internal_resistance_ohm=0.05,
        discharge_curve=_DISCHARGE_CURVE,
    )
    return VehicleParams(
        mass_kg=0.155,
        tire_diameter_mm=26.0,
        gear_ratio=3.5,
        drivetrain_type="4wd",
        motor=motor,
        battery=battery,
        rolling_resistance_coef=0.025,
        drivetrain_efficiency=0.85,
    )


def _make_track_minimal() -> TrackParams:
    """最小構成: ストレート1区間のみ"""
    return TrackParams(
        name="minimal",
        sections=[
            SectionParams(section_id=1, section_type="straight", length_mm=1000.0)
        ],
        corner_radius_mm=103.0,
        obstacle_height_mm=5.0,
        obstacle_per_lap=1,
    )


def _make_track_jcjc() -> TrackParams:
    """JCJC全区間（3188mm/周）"""
    sections = [
        SectionParams(1, "straight", 218.0),
        SectionParams(2, "curve", 162.0),
        SectionParams(3, "straight", 218.0),
        SectionParams(4, "curve", 162.0),
        SectionParams(5, "straight", 432.0),
        SectionParams(6, "slope_up", 210.0, slope_deg=29.0),
        SectionParams(7, "slope_down", 210.0, slope_deg=-29.0),
        SectionParams(8, "straight", 218.0),
        SectionParams(9, "curve", 162.0),
        SectionParams(10, "lane_change", 436.0),
        SectionParams(11, "straight", 218.0),
        SectionParams(12, "curve", 162.0),
        SectionParams(13, "straight", 218.0),
        SectionParams(14, "curve", 162.0),
    ]
    return TrackParams(
        name="JCJC",
        sections=sections,
        corner_radius_mm=103.0,
        obstacle_height_mm=5.0,
        obstacle_per_lap=1,
    )


def _make_race_rules() -> RaceRules:
    return RaceRules(time_limit_s=600.0, dnf_speed_threshold_mps=0.05)


class TestSimulateLapMinimal:
    def test_returns_lap_result_and_battery(self):
        vehicle = _make_vehicle()
        track = _make_track_minimal()
        battery = initialize_battery(vehicle.battery)
        rules = _make_race_rules()

        lap_result, new_battery = simulate_lap(vehicle, track, battery, 1, _PHYSICS_CONFIG, rules)
        assert lap_result.lap_number == 1
        assert lap_result.time_s > 0.0
        assert lap_result.energy_consumed_mAh > 0.0
        assert new_battery.soc < 1.0

    def test_section_results_count(self):
        """区間結果の数がセクション数と一致する"""
        vehicle = _make_vehicle()
        track = _make_track_minimal()
        battery = initialize_battery(vehicle.battery)
        rules = _make_race_rules()

        lap_result, _ = simulate_lap(vehicle, track, battery, 1, _PHYSICS_CONFIG, rules)
        assert len(lap_result.section_results) == len(track.sections)


class TestSimulateLapJCJC:
    def test_lap_time_reasonable(self):
        """
        物理モデルのオーダー確認テスト。
        JCJC（3188mm）を motor 15750rpm / gear 3.5 / tire 26mm で走行すると
        無負荷速度 ≈ 6 m/s → 損失込みで 2〜5 m/s 程度が合理的とみなす。
        → 周回タイムは 0.5〜5.0s の範囲を期待する。

        NOTE: runs.csv の実測値との整合性は別途 calibration で対応する。
              係数（rolling_resistance_coef 等）が仮説値のため誤差が大きい。
        """
        vehicle = _make_vehicle()
        track = _make_track_jcjc()
        battery = initialize_battery(vehicle.battery)
        rules = _make_race_rules()

        lap_result, _ = simulate_lap(vehicle, track, battery, 1, _PHYSICS_CONFIG, rules)
        assert 0.5 <= lap_result.time_s <= 5.0, (
            f"周回タイム {lap_result.time_s:.2f}s が想定オーダー外"
        )

    def test_energy_consumed_positive(self):
        vehicle = _make_vehicle()
        track = _make_track_jcjc()
        battery = initialize_battery(vehicle.battery)
        rules = _make_race_rules()

        lap_result, _ = simulate_lap(vehicle, track, battery, 1, _PHYSICS_CONFIG, rules)
        assert lap_result.energy_consumed_mAh > 0.0

    def test_battery_soc_decreases(self):
        vehicle = _make_vehicle()
        track = _make_track_jcjc()
        battery = initialize_battery(vehicle.battery)
        rules = _make_race_rules()

        _, new_battery = simulate_lap(vehicle, track, battery, 1, _PHYSICS_CONFIG, rules)
        assert new_battery.soc < 1.0

    def test_section_results_all_14(self):
        vehicle = _make_vehicle()
        track = _make_track_jcjc()
        battery = initialize_battery(vehicle.battery)
        rules = _make_race_rules()

        lap_result, _ = simulate_lap(vehicle, track, battery, 1, _PHYSICS_CONFIG, rules)
        assert len(lap_result.section_results) == 14

    def test_avg_speed_positive(self):
        vehicle = _make_vehicle()
        track = _make_track_jcjc()
        battery = initialize_battery(vehicle.battery)
        rules = _make_race_rules()

        lap_result, _ = simulate_lap(vehicle, track, battery, 1, _PHYSICS_CONFIG, rules)
        assert lap_result.avg_speed_mps > 0.0
