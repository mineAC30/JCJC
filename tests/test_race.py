"""
レースシミュレーションのテスト

レース全体（複数周回）の挙動を検証する。
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
from sim_core.simulation.race import simulate_race

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


def _make_track_jcjc() -> TrackParams:
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


class TestSimulateRace:
    def test_returns_race_result(self):
        vehicle = _make_vehicle()
        track = _make_track_jcjc()
        rules = RaceRules(time_limit_s=600.0)

        result = simulate_race(vehicle, track, rules, _PHYSICS_CONFIG)
        assert result.total_laps >= 0

    def test_total_time_within_limit(self):
        """総走行時間が制限時間以内に収まる"""
        vehicle = _make_vehicle()
        track = _make_track_jcjc()
        rules = RaceRules(time_limit_s=600.0)

        result = simulate_race(vehicle, track, rules, _PHYSICS_CONFIG)
        assert result.total_time_s <= rules.time_limit_s

    def test_longer_time_gives_more_laps(self):
        """制限時間が長い方が周回数が多くなる（または同じ）"""
        vehicle = _make_vehicle()
        track = _make_track_jcjc()

        result_short = simulate_race(vehicle, track, RaceRules(time_limit_s=60.0), _PHYSICS_CONFIG)
        result_long = simulate_race(vehicle, track, RaceRules(time_limit_s=120.0), _PHYSICS_CONFIG)
        assert result_long.total_laps >= result_short.total_laps

    def test_lap_results_count_matches_total_laps(self):
        """lap_results の件数が total_laps と一致する"""
        vehicle = _make_vehicle()
        track = _make_track_jcjc()
        rules = RaceRules(time_limit_s=120.0)

        result = simulate_race(vehicle, track, rules, _PHYSICS_CONFIG)
        assert len(result.lap_results) == result.total_laps

    def test_no_dnf_on_standard_run(self):
        """通常条件（NiMH 2400mAh / 10分）では DNF にならない"""
        vehicle = _make_vehicle()
        track = _make_track_jcjc()
        rules = RaceRules(time_limit_s=600.0)

        result = simulate_race(vehicle, track, rules, _PHYSICS_CONFIG)
        assert not result.dnf

    def test_zero_time_limit_gives_zero_laps(self):
        """制限時間ゼロでは周回数がゼロ"""
        vehicle = _make_vehicle()
        track = _make_track_jcjc()
        rules = RaceRules(time_limit_s=0.0)

        result = simulate_race(vehicle, track, rules, _PHYSICS_CONFIG)
        assert result.total_laps == 0
