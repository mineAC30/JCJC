"""
レースシミュレーションモジュール

制限時間内に何周できるかをシミュレーションする。

【アルゴリズム】
    1. 電池を初期化する
    2. 制限時間内に simulate_lap を繰り返す
    3. 各周回後に完走不能チェックを行う
    4. 制限時間を超えた周回は部分完了とみなさない（完了した周回のみカウント）
    5. RaceResult を返す
"""

from __future__ import annotations

from typing import Dict

from ..domain.params import RaceRules, TrackParams, VehicleParams
from ..domain.results import RaceResult
from ..physics import battery as battery_physics
from . import lap as lap_simulator


def simulate_race(
    vehicle_params: VehicleParams,
    track_params: TrackParams,
    race_rules: RaceRules,
    physics_config: Dict,
) -> RaceResult:
    """
    レース全体のシミュレーションを行う。

    入力:
        vehicle_params : 車体パラメータ
        track_params   : コースパラメータ
        race_rules     : レースレギュレーション（制限時間・DNF基準）
        physics_config : 物理係数設定

    出力:
        RaceResult（総周回数・タイム・各周結果・DNF情報を含む）

    仮定:
        - 残り時間が1周に足りない場合でも、その周が始まったとみなして走行する
        - 制限時間を超えた周回は総周回数にカウントしない
    """
    battery_state = battery_physics.initialize_battery(vehicle_params.battery)

    lap_results = []
    elapsed_time_s = 0.0
    lap_number = 1

    while elapsed_time_s < race_rules.time_limit_s:
        lap_result, battery_state = lap_simulator.simulate_lap(
            vehicle_params=vehicle_params,
            track_params=track_params,
            battery_state=battery_state,
            lap_number=lap_number,
            physics_config=physics_config,
            race_rules=race_rules,
        )

        # 完走不能チェック
        if lap_result.avg_speed_mps < race_rules.dnf_speed_threshold_mps:
            return RaceResult(
                total_laps=len(lap_results),
                total_time_s=elapsed_time_s,
                lap_results=lap_results,
                dnf=True,
                dnf_reason=(
                    f"周回 {lap_number} で速度不足"
                    f"（avg {lap_result.avg_speed_mps:.3f} m/s < "
                    f"{race_rules.dnf_speed_threshold_mps} m/s）"
                ),
            )

        elapsed_time_s += lap_result.time_s

        # 制限時間内に完了した周回のみカウント
        if elapsed_time_s <= race_rules.time_limit_s:
            lap_results.append(lap_result)
            lap_number += 1
        else:
            # 制限時間超過：最後の周回はカウントせず終了
            elapsed_time_s -= lap_result.time_s
            break

    return RaceResult(
        total_laps=len(lap_results),
        total_time_s=elapsed_time_s,
        lap_results=lap_results,
        dnf=False,
    )
