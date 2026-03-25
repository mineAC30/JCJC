"""
感度分析モジュール（骨格）

各パラメータが総周回数に与える影響を定量化する。
Phase 4 以降で実装する。

現時点では:
    - 1パラメータを±x% 変化させたときの周回数変化率を計算する関数の骨格を用意する。
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from typing import Callable, Dict, List, Tuple

from ..domain.params import RaceRules, TrackParams, VehicleParams
from ..domain.results import RaceResult


def one_parameter_sensitivity(
    simulate_fn: Callable[..., RaceResult],
    vehicle_params: VehicleParams,
    track_params: TrackParams,
    race_rules: RaceRules,
    physics_config: Dict,
    param_path: List[str],
    delta_ratio: float = 0.10,
) -> Tuple[float, float, float]:
    """
    1パラメータの ±delta_ratio 変化に対する周回数の感度を計算する。

    入力:
        simulate_fn   : simulate_race 関数（または互換インターフェース）
        vehicle_params: ベース車体パラメータ
        track_params  : コースパラメータ
        race_rules    : レースレギュレーション
        physics_config: 物理係数設定
        param_path    : 変化させるパラメータのパス（例: ['motor', 'no_load_rpm']）
        delta_ratio   : 変化量の比率（デフォルト ±10%）

    出力:
        (base_laps, plus_laps, minus_laps)
        - base_laps  : ベース周回数
        - plus_laps  : +delta_ratio 時の周回数
        - minus_laps : -delta_ratio 時の周回数

    注意:
        この関数は param_path に対してディープコピーと手動代入を行う。
        現時点では motor/battery の1階層のみ対応。
        複雑なネスト構造への対応は今後拡張する。
    """
    base_result = simulate_fn(vehicle_params, track_params, race_rules, physics_config)
    base_laps = float(base_result.total_laps)

    # パラメータの現在値を取得
    obj = vehicle_params
    for key in param_path[:-1]:
        obj = getattr(obj, key)
    base_value = getattr(obj, param_path[-1])

    if not isinstance(base_value, (int, float)):
        raise TypeError(f"param_path {param_path} が数値を指していません")

    def _run_with_value(new_value: float) -> float:
        vp = deepcopy(vehicle_params)
        target = vp
        for key in param_path[:-1]:
            target = getattr(target, key)
        # dataclass のフィールドを直接上書き（簡易実装）
        object.__setattr__(target, param_path[-1], new_value)
        result = simulate_fn(vp, track_params, race_rules, physics_config)
        return float(result.total_laps)

    plus_laps = _run_with_value(base_value * (1.0 + delta_ratio))
    minus_laps = _run_with_value(base_value * (1.0 - delta_ratio))

    return base_laps, plus_laps, minus_laps
