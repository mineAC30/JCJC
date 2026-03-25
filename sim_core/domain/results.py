"""
結果データ構造モジュール

シミュレーション結果を格納する dataclass を定義する。
区間 → 1周 → レース全体 の階層構造。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class SectionResult:
    """
    1区間の走行結果

    単位:
        time_s               : [s]
        energy_consumed_mAh  : [mAh]
        avg_speed_mps        : [m/s]
        speed_loss_mps       : [m/s]（コーナー・段差等による速度低下量）
    """

    section_id: int
    section_type: str
    time_s: float
    energy_consumed_mAh: float
    avg_speed_mps: float
    speed_loss_mps: float = 0.0
    slip_angle_rad: float = 0.0         # タイヤスリップ角 [rad]（curve のみ。TireParams がある場合）
    roller_side_force_N: float = 0.0    # ローラー側面力 [N]（ローラーあり curve のみ）


@dataclass
class LapResult:
    """
    1周の走行結果

    単位:
        time_s               : [s]
        energy_consumed_mAh  : [mAh]
        avg_speed_mps        : [m/s]
    """

    lap_number: int
    time_s: float
    energy_consumed_mAh: float
    avg_speed_mps: float
    section_results: List[SectionResult] = field(default_factory=list)


@dataclass
class RaceResult:
    """
    レース全体の結果

    単位:
        total_time_s         : [s]
    """

    total_laps: int
    total_time_s: float
    lap_results: List[LapResult] = field(default_factory=list)
    dnf: bool = False
    dnf_reason: str = ""
