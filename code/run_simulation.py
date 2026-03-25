#!/usr/bin/env python3
"""
ミニ四駆レースシミュレーション実行スクリプト

【使い方】
    # プロジェクトルートから実行
    python code/run_simulation.py

    # オプション指定
    python code/run_simulation.py --time-limit 1200 --verbose
    python code/run_simulation.py --no-plot        # グラフ出力をスキップ

【出力】
    data/output/{YYYYMMDD_HHMMSS}_{motor_name}/
        summary_plots.png     # 全グラフ（6パネル）
        section_data.csv      # 全セクション詳細データ
        lap_summary.csv       # ラップごとのサマリー
        configs/              # 使用した YAML 設定ファイルのコピー
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

# プロジェクトルートを sys.path に追加
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# code/ ディレクトリも sys.path に追加（plot モジュール参照用）
_CODE_DIR = Path(__file__).resolve().parent
if str(_CODE_DIR) not in sys.path:
    sys.path.insert(0, str(_CODE_DIR))

import argparse

from sim_core.io.config_loader import (
    load_physics_config,
    load_race_rules,
    load_track_params,
    load_vehicle_params,
)
from sim_core.io.logger import log_lap_result, log_race_summary, setup_logger
from sim_core.simulation.race import simulate_race
from sim_core.evaluation.scorer import score_race
from sim_core.domain.params import RaceRules


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ミニ四駆レースシミュレーション実行スクリプト",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--vehicle",
        default="configs/vehicle_example.yaml",
        help="車体設定 YAML ファイルのパス（プロジェクトルートからの相対パス）",
    )
    parser.add_argument(
        "--track",
        default="configs/track_jcjc.yaml",
        help="コース設定 YAML ファイルのパス",
    )
    parser.add_argument(
        "--config",
        default="configs/default.yaml",
        help="デフォルト設定 YAML ファイルのパス",
    )
    parser.add_argument(
        "--time-limit",
        type=float,
        default=None,
        metavar="SECONDS",
        help="制限時間 [s]（例: 600=10分, 1200=20分）",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="各周回の詳細を出力する",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="グラフ・CSV 出力をスキップする",
    )
    args = parser.parse_args()

    import logging
    logger = setup_logger(level=logging.DEBUG if args.verbose else logging.INFO)

    # 設定読み込み（パスはプロジェクトルート起点）
    root = _ROOT
    vehicle_params = load_vehicle_params(root / args.vehicle)
    track_params = load_track_params(root / args.track)
    race_rules = load_race_rules(root / args.config)
    physics_config = load_physics_config(root / args.config)

    if args.time_limit is not None:
        from dataclasses import replace
        race_rules = replace(race_rules, time_limit_s=args.time_limit)

    logger.info(
        "実行設定: コース=%s / 制限時間=%.0f s / モーター=%s / 車体=%.0f g",
        track_params.name,
        race_rules.time_limit_s,
        vehicle_params.motor.name,
        vehicle_params.mass_kg * 1000,
    )
    logger.info("コース全長: %.0f mm / 1周", track_params.lap_length_mm)

    result = simulate_race(vehicle_params, track_params, race_rules, physics_config)

    if args.verbose:
        for lap in result.lap_results:
            log_lap_result(logger, lap)

    log_race_summary(logger, result, race_rules.time_limit_s)

    # 評価指標の表示
    scores = score_race(result, race_rules)
    logger.info("評価指標: %s", scores)

    # ──────────────────────────────────────────────
    # グラフ・CSV 出力
    # ──────────────────────────────────────────────
    if not args.no_plot:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        motor_slug = vehicle_params.motor.name.replace(" ", "_")
        output_dir = root / "data" / "output" / f"{timestamp}_{motor_slug}"

        try:
            from plot.lap_plots import plot_all
            from plot.save_run import save_all

            logger.info("グラフ・データを出力中: %s", output_dir)

            plot_path = plot_all(
                result,
                output_dir,
                title_prefix=vehicle_params.motor.name,
            )
            saved = save_all(
                result,
                output_dir,
                yaml_paths={
                    "vehicle": root / args.vehicle,
                    "track":   root / args.track,
                    "config":  root / args.config,
                },
            )

            logger.info("出力完了:")
            logger.info("  グラフ         : %s", plot_path)
            logger.info("  セクションCSV  : %s", saved["section_csv"])
            logger.info("  ラップCSV      : %s", saved["lap_csv"])
            logger.info("  設定コピー先   : %s", saved["config_dir"])

        except ImportError as e:
            logger.warning("グラフ出力をスキップ（ライブラリ不足: %s）", e)
            logger.warning("matplotlib をインストールしてください: pip install matplotlib")


if __name__ == "__main__":
    main()
