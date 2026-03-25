"""
状態量定義モジュール

走行中に時々刻々と変化する状態量を dataclass で定義する。
パラメータ (params.py) との分離がポイント：
  - params : 設計・設定値（走行中に変わらない）
  - state  : 走行中の物理状態（時間とともに変化する）
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class BatteryState:
    """
    電池の現在状態

    単位:
        voltage_v             : [V]（開路電圧）
        charge_remaining_mAh  : [mAh]
        soc                   : 無次元 [0-1]
        total_consumed_mAh    : [mAh]（累積消費量）
    """

    voltage_v: float
    charge_remaining_mAh: float
    soc: float
    total_consumed_mAh: float = 0.0


@dataclass
class VehicleState:
    """
    車体の現在状態

    単位:
        speed_mps           : [m/s]
        elapsed_time_s      : [s]
        position_in_lap_m   : [m]（現在周回内での進行距離）
        lap_count           : 完了周回数（無次元）
    """

    speed_mps: float
    elapsed_time_s: float
    lap_count: int
    position_in_lap_m: float = 0.0
