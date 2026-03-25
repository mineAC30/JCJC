"""
スコアリングモジュール

レース結果を評価指標（周回数・平均周回タイム等）に変換する。
最適化フェーズでの目的関数として利用することを想定している。
"""

from __future__ import annotations

from typing import Dict

from ..domain.params import RaceRules
from ..domain.results import RaceResult


def score_race(result: RaceResult, race_rules: RaceRules) -> Dict[str, float]:
    """
    レース結果から評価指標を計算して返す。

    入力:
        result     : レースシミュレーション結果
        race_rules : レースレギュレーション

    出力:
        評価指標の辞書:
            total_laps        : 総周回数（最大化したい主指標）
            avg_lap_time_s    : 平均周回タイム [s]
            time_utilization  : 使用時間 / 制限時間 [0-1]
            dnf               : 完走不能フラグ (0 or 1)
    """
    avg_lap_time_s = (
        result.total_time_s / result.total_laps
        if result.total_laps > 0
        else float("inf")
    )
    time_utilization = result.total_time_s / race_rules.time_limit_s

    return {
        "total_laps": float(result.total_laps),
        "avg_lap_time_s": avg_lap_time_s,
        "time_utilization": time_utilization,
        "dnf": 1.0 if result.dnf else 0.0,
    }
