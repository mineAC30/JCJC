#!/usr/bin/env python3
"""
ミニ四駆レースシミュレーション CLI

使い方:
    python -m mini4wd_opt.cli.run_simulation \\
        --vehicle configs/vehicle_example.yaml \\
        --track   configs/track_jcjc.yaml \\
        --config  configs/default.yaml \\
        [--time-limit 600]

オプションで --time-limit を渡すと default.yaml の設定を上書きできる。
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from ..io.config_loader import (
    load_physics_config,
    load_race_rules,
    load_track_params,
    load_vehicle_params,
)
from ..io.logger import log_lap_result, log_race_summary, setup_logger
from ..simulation.race import simulate_race


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="ミニ四駆レースシミュレーション"
    )
    parser.add_argument(
        "--vehicle",
        type=Path,
        default=Path("configs/vehicle_example.yaml"),
        help="車体設定 YAML ファイルのパス",
    )
    parser.add_argument(
        "--track",
        type=Path,
        default=Path("configs/track_jcjc.yaml"),
        help="コース設定 YAML ファイルのパス",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/default.yaml"),
        help="デフォルト設定 YAML ファイルのパス",
    )
    parser.add_argument(
        "--time-limit",
        type=float,
        default=None,
        help="制限時間 [s]（指定時に YAML の設定を上書き）",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="各周回の詳細を出力する",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    logger = setup_logger(level=logging.DEBUG if args.verbose else logging.INFO)

    logger.info("設定ファイルを読み込んでいます...")
    vehicle_params = load_vehicle_params(args.vehicle)
    track_params = load_track_params(args.track)
    race_rules = load_race_rules(args.config)
    physics_config = load_physics_config(args.config)

    if args.time_limit is not None:
        from dataclasses import replace
        race_rules = replace(race_rules, time_limit_s=args.time_limit)

    logger.info(
        "シミュレーション開始: コース=%s, 制限時間=%.0f s",
        track_params.name,
        race_rules.time_limit_s,
    )
    logger.info(
        "コース全長: %.0f mm / 1周",
        track_params.lap_length_mm,
    )

    result = simulate_race(vehicle_params, track_params, race_rules, physics_config)

    if args.verbose:
        for lap in result.lap_results:
            log_lap_result(logger, lap)

    log_race_summary(logger, result, race_rules.time_limit_s)


if __name__ == "__main__":
    main()
