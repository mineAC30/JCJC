"""
ログ出力モジュール

シミュレーション結果を標準ロガーと構造化テキストで出力する。
"""

from __future__ import annotations

import logging
from typing import Optional

from ..domain.results import LapResult, RaceResult


def setup_logger(
    name: str = "mini4wd_opt",
    level: int = logging.INFO,
) -> logging.Logger:
    """
    ロガーをセットアップして返す。

    入力:
        name  : ロガー名
        level : ログレベル（logging.DEBUG / INFO / WARNING 等）

    出力:
        設定済み Logger
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        )
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def log_lap_result(
    logger: logging.Logger,
    result: LapResult,
) -> None:
    """
    1周の結果をログに出力する。

    入力:
        logger : Logger インスタンス
        result : LapResult
    """
    logger.info(
        "Lap %3d | time=%6.2f s | energy=%6.2f mAh | avg=%.3f m/s",
        result.lap_number,
        result.time_s,
        result.energy_consumed_mAh,
        result.avg_speed_mps,
    )


def log_race_summary(
    logger: logging.Logger,
    result: RaceResult,
    time_limit_s: Optional[float] = None,
) -> None:
    """
    レース結果のサマリーをログに出力する。

    入力:
        logger       : Logger インスタンス
        result       : RaceResult
        time_limit_s : 制限時間 [s]（指定時に残り時間を表示）
    """
    logger.info("=" * 50)
    logger.info("Race Summary")
    logger.info("  Total laps   : %d", result.total_laps)
    logger.info("  Total time   : %.2f s", result.total_time_s)
    if result.total_laps > 0:
        logger.info(
            "  Avg lap time : %.2f s", result.total_time_s / result.total_laps
        )
    if time_limit_s is not None:
        logger.info(
            "  Remaining    : %.2f s", time_limit_s - result.total_time_s
        )
    if result.dnf:
        logger.warning("  DNF: %s", result.dnf_reason)
    logger.info("=" * 50)
