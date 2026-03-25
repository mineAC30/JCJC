"""
コーナリングモデル

仮定（最大コーナー速度モデル）:
    コーナーで安定走行できる最大速度 = sqrt(μ × g × r)

    ここで:
        μ : 横方向摩擦係数 [無次元・仮説値]
        g : 重力加速度 [m/s²]
        r : コーナー半径 [m]

    この式は定常円旋回（スリップなし）を前提とした上限値である。
    実際はコース設計・ローラー配置・車体剛性等に依存するため、
    係数 μ を実走データで補正すること。
"""

import math

_GRAVITY_MPS2 = 9.81  # 重力加速度 [m/s²]


def compute_max_corner_speed_mps(
    corner_radius_mm: float,
    friction_coefficient: float = 0.80,
) -> float:
    """
    コーナーで安定走行できる最大速度を計算する。

    入力:
        corner_radius_mm    : コーナー半径 [mm]
        friction_coefficient: 横方向摩擦係数 [無次元・仮説値]

    出力:
        最大コーナー速度 [m/s]
    """
    corner_radius_m = corner_radius_mm / 1000.0
    return math.sqrt(friction_coefficient * _GRAVITY_MPS2 * corner_radius_m)


def compute_corner_speed_loss_mps(
    approach_speed_mps: float,
    corner_radius_mm: float,
    friction_coefficient: float = 0.80,
) -> float:
    """
    コーナーでの速度低下量を計算する。

    入力:
        approach_speed_mps  : コーナー進入速度 [m/s]
        corner_radius_mm    : コーナー半径 [mm]
        friction_coefficient: 横方向摩擦係数 [無次元・仮説値]

    出力:
        速度低下量 [m/s]（正値 = 減速。0以上）
    """
    v_max = compute_max_corner_speed_mps(corner_radius_mm, friction_coefficient)
    if approach_speed_mps > v_max:
        return approach_speed_mps - v_max
    return 0.0
