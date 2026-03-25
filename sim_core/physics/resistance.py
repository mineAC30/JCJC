"""
走行抵抗モデル

転がり抵抗と傾斜による重力成分を計算する。

仮定:
    - 転がり抵抗係数は速度・温度によらず一定 [仮説値]
    - 空気抵抗は無視する（ミニ四駆スケールでは支配的でないと仮定）
"""

import math

_GRAVITY_MPS2 = 9.81  # 重力加速度 [m/s²]


def compute_rolling_resistance_N(
    mass_kg: float,
    rolling_resistance_coef: float,
    slope_deg: float = 0.0,
) -> float:
    """
    転がり抵抗力を計算する。

    入力:
        mass_kg                 : 車体質量 [kg]
        rolling_resistance_coef : 転がり抵抗係数 [無次元・仮説値]
        slope_deg               : 傾斜角 [deg]（登り=正、下り=負）

    出力:
        転がり抵抗力 [N]（走行方向に対して逆向き、常に正値）

    仮定:
        F_roll = mu_roll × m × g × cos(slope)
    """
    cos_slope = math.cos(math.radians(slope_deg))
    return rolling_resistance_coef * mass_kg * _GRAVITY_MPS2 * cos_slope


def compute_gravity_component_N(
    mass_kg: float,
    slope_deg: float,
) -> float:
    """
    傾斜における重力の走行方向成分を計算する。

    入力:
        mass_kg   : 車体質量 [kg]
        slope_deg : 傾斜角 [deg]（登り=正、下り=負）

    出力:
        重力の走行方向成分 [N]（登り=正=抵抗力、下り=負=推進力）

    仮定:
        F_gravity = m × g × sin(slope)
    """
    return mass_kg * _GRAVITY_MPS2 * math.sin(math.radians(slope_deg))
