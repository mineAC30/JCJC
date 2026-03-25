"""
段差（ゴム障害物）通過モデル

仮定（簡易衝突モデル）:
    段差通過時の速度低下量 = loss_coefficient × sqrt(2 × g × h)
    
    ここで:
        h               : 段差高さ [m]
        loss_coefficient: 速度低下係数（無次元）[仮説値・要実測補正]

    この係数は単純な障害物衝突の特性速度スケールを用いており、
    実際の車体の姿勢変化・振動・バウンド等は捨象している。
    実走データとの比較で loss_coefficient を調整すること。
"""

import math

_GRAVITY_MPS2 = 9.81  # 重力加速度 [m/s²]


def compute_obstacle_speed_loss_mps(
    obstacle_height_mm: float,
    approach_speed_mps: float,
    loss_coefficient: float = 0.15,
) -> float:
    """
    段差通過後の速度低下量を計算する（簡易モデル）。

    入力:
        obstacle_height_mm : 段差高さ [mm]
        approach_speed_mps : 突入速度 [m/s]
        loss_coefficient   : 速度低下係数 [無次元・仮説値]（デフォルト 0.15）

    出力:
        速度低下量 [m/s]（正値 = 減速。突入速度を超えることはない）

    仮定:
        characteristic_speed = sqrt(2 × g × h)
        speed_loss = loss_coefficient × characteristic_speed
    """
    obstacle_height_m = obstacle_height_mm / 1000.0
    characteristic_speed_mps = math.sqrt(2.0 * _GRAVITY_MPS2 * obstacle_height_m)
    speed_loss = loss_coefficient * characteristic_speed_mps
    return min(speed_loss, approach_speed_mps)
