#!/usr/bin/env python3
"""
sim-core.py — エントリーポイント（後方互換ラッパー）

実体は sim_core/main.py に移動しました。
このファイルは後方互換のために残してあります。

【使い方】
    # 直接実行（従来通り）
    python sim-core.py
    python sim-core.py --vehicle configs/vehicle_example.yaml --time-limit 1200 --verbose

    # 関数インポート（従来通り）
    from sim-core import run, score  # ※ハイフン付きは直接 import 不可。
    # → 代わりに: from sim_core.main import run, score
"""

from __future__ import annotations

import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

# 全 API を sim_core.main から再エクスポート
from sim_core.main import run, score  # noqa: F401

if __name__ == "__main__":
    from sim_core.main import _parse_args
    args = _parse_args()
    run(
        vehicle_yaml=args.vehicle,
        track_yaml=args.track,
        config_yaml=args.config,
        time_limit_s=args.time_limit,
        verbose=args.verbose,
    )

