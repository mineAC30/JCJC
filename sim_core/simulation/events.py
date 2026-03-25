"""
走行イベント定義モジュール

走行中に発生するイベントを列挙型と dataclass で定義する。
ログ・デバッグ・感度分析での利用を想定している。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class EventType(Enum):
    """走行中に発生するイベントの種類"""

    OBSTACLE_HIT = auto()   # 段差（ゴム障害物）通過
    CORNER_LIMITED = auto() # コーナーで速度制限が適用された
    LANE_CHANGE = auto()    # レーンチェンジ通過（速度低下あり）
    SLOPE_UP = auto()       # 登りスロープ開始
    SLOPE_DOWN = auto()     # 下りスロープ開始
    LAP_COMPLETE = auto()   # 周回完了
    DNF = auto()            # 完走不能（速度不足・電池切れ）


@dataclass
class RaceEvent:
    """
    レース中に発生した1イベントの記録

    単位:
        elapsed_time_s    : [s]（レース開始からの経過時間）
        speed_before_mps  : [m/s]
        speed_after_mps   : [m/s]
    """

    elapsed_time_s: float
    lap_number: int
    event_type: EventType
    speed_before_mps: float
    speed_after_mps: float
    note: str = ""
