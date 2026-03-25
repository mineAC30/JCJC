"""
sim_core/main.py — ミニ四駆レースシミュレーション API & CLI

旧 sim-core.py (プロジェクトルート) から移動。
プロジェクトルートからの相対パスを確実に解決する。

使い方:
    # ルートエントリーポイント経由（後方互換）
    python sim-core.py

    # パッケージとして直接実行
    python -m sim_core.main

    # 関数インポート
    from sim_core.main import run, score
"""

from __future__ import annotations

import sys
from pathlib import Path

# プロジェクトルート = sim_core/ の親ディレクトリ
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from sim_core.domain.params import RaceRules
from sim_core.domain.results import RaceResult
from sim_core.evaluation.scorer import score_race
from sim_core.io.config_loader import (
    load_physics_config,
    load_race_rules,
    load_track_params,
    load_vehicle_params,
)
from sim_core.io.logger import log_lap_result, log_race_summary, setup_logger
from sim_core.simulation.race import simulate_race


# ──────────────────────────────────────────────
# 公開 API
# ──────────────────────────────────────────────

def run(
    vehicle_yaml: Path | str = "configs/vehicle_example.yaml",
    track_yaml: Path | str = "configs/track_jcjc.yaml",
    config_yaml: Path | str = "configs/default.yaml",
    time_limit_s: float | None = None,
    verbose: bool = False,
    root: Path | None = None,
) -> RaceResult:
    """
    シミュレーションを実行して結果を返す。

    入力:
        vehicle_yaml : 車体設定 YAML のパス（root 起点の相対パス またはフルパス）
        track_yaml   : コース設定 YAML のパス
        config_yaml  : デフォルト設定 YAML のパス
        time_limit_s : 制限時間 [s]（None の場合は YAML の設定を使用）
        verbose      : 各周回の詳細を標準出力に出力するか
        root         : プロジェクトルート（None の場合は自動検出）

    出力:
        RaceResult
    """
    import logging

    logger = setup_logger(level=logging.DEBUG if verbose else logging.INFO)

    if root is None:
        root = _ROOT

    root = Path(root)
    vehicle_params = load_vehicle_params(root / vehicle_yaml)
    track_params = load_track_params(root / track_yaml)
    race_rules = load_race_rules(root / config_yaml)
    physics_config = load_physics_config(root / config_yaml)

    if time_limit_s is not None:
        from dataclasses import replace
        race_rules = replace(race_rules, time_limit_s=time_limit_s)

    logger.info(
        "実行設定: コース=%s / 制限時間=%.0f s / モーター=%s / 車体=%.0f g",
        track_params.name,
        race_rules.time_limit_s,
        vehicle_params.motor.name,
        vehicle_params.mass_kg * 1000,
    )
    logger.info("コース全長: %.0f mm / 1周", track_params.lap_length_mm)

    result = simulate_race(vehicle_params, track_params, race_rules, physics_config)

    if verbose:
        for lap in result.lap_results:
            log_lap_result(logger, lap)

    log_race_summary(logger, result, race_rules.time_limit_s)
    return result


def score(result: RaceResult, time_limit_s: float) -> dict:
    """
    RaceResult から評価指標を計算して返す。

    入力:
        result       : simulate_race または run() の戻り値
        time_limit_s : 制限時間 [s]

    出力:
        評価指標の辞書（total_laps, avg_lap_time_s, time_utilization, dnf）
    """
    rules = RaceRules(time_limit_s=time_limit_s)
    return score_race(result, rules)


# ──────────────────────────────────────────────
# CLI エントリーポイント
# ──────────────────────────────────────────────

def _parse_args():
    import argparse

    parser = argparse.ArgumentParser(
        description="ミニ四駆レースシミュレーション",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--vehicle",
        default="configs/vehicle_example.yaml",
        help="車体設定 YAML ファイルのパス",
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
        help="制限時間 [s]（指定時は YAML の設定を上書き）",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="各周回の詳細を出力する",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run(
        vehicle_yaml=args.vehicle,
        track_yaml=args.track,
        config_yaml=args.config,
        time_limit_s=args.time_limit,
        verbose=args.verbose,
    )
