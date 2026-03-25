"""
パラメータ定義モジュール

このプロジェクトで扱う物理パラメータ群を dataclass で定義する。
各フィールドには単位をコメントで明示する。

仮説値は「[仮説値]」と注記すること。設計者が実測・確認した値は注記を外す。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Literal, Optional, Tuple


@dataclass
class MotorParams:
    """
    DCモーターの特性パラメータ（線形モデル）

    仮定:
        - トルク-回転数特性は線形（直流整流子モーター近似）
        - 定格電圧に対して比例スケーリングする

    単位:
        no_load_rpm         : [rpm]
        stall_torque_Nmm    : [N·mm]
        no_load_current_A   : [A]
        stall_current_A     : [A]
        rated_voltage_v     : [V]
    """

    name: str
    no_load_rpm: float
    stall_torque_Nmm: float
    no_load_current_A: float
    stall_current_A: float
    rated_voltage_v: float


@dataclass
class BatteryParams:
    """
    電池の特性パラメータ

    仮定:
        - 内部抵抗は一定（温度・劣化による変動を無視）
        - 放電曲線は線形補間する

    単位:
        nominal_voltage_v       : [V]（2本直列の合計電圧）
        capacity_mAh            : [mAh]
        internal_resistance_ohm : [Ω]
    """

    battery_type: str  # 'NiMH' or 'alkaline'
    nominal_voltage_v: float
    capacity_mAh: float
    internal_resistance_ohm: float
    # SOC vs 開路電圧の放電曲線 [(soc 0-1, voltage_v), ...]
    discharge_curve: List[Tuple[float, float]] = field(default_factory=list)


@dataclass
class TireParams:
    """
    タイヤ特性パラメータ

    仮定:
        - 摩擦係数は速度・温度によらず一定 [仮説値]
        - コーナリングスティフネスは荷重依存性を無視した定数 [仮説値]
        - 転がり抵抗係数は材質によって異なる [仮説値]

    単位:
        diameter_mm                  : [mm]
        width_mm                     : [mm]
        friction_coef                : 無次元（横方向摩擦係数）[仮説値]
        rolling_resistance_coef      : 無次元 [仮説値]
        cornering_stiffness_N_per_rad: [N/rad] [仮説値]
    """

    name: str
    diameter_mm: float
    width_mm: float
    material: str                                   # "hard" / "medium" / "soft" / "sponge" / "super_hard"
    friction_coef: float = 0.80                     # 横方向摩擦係数 [仮説値]
    rolling_resistance_coef: float = 0.025          # 転がり抵抗係数 [仮説値]
    cornering_stiffness_N_per_rad: float = 8.0      # コーナリングスティフネス [仮説値]


@dataclass
class RollerConfig:
    """
    ローラー配置パラメータ

    ミニ四駆のローラーはコースガイドレールに接触し、
    タイヤ横力限界を超えた横力を補助する。

    単位:
        front_diameter_mm             : [mm]
        rear_diameter_mm              : [mm]
        front_position_from_axle_mm   : フロント軸から前方距離 [mm] [仮説値]
        rear_position_from_axle_mm    : リア軸から後方距離 [mm] [仮説値]
        track_width_mm                : 左右ローラー外端間距離 [mm] [仮説値]
        front_friction_coef           : 無次元 [仮説値]
        rear_friction_coef            : 無次元 [仮説値]
    """

    front_diameter_mm: float
    rear_diameter_mm: float
    front_position_from_axle_mm: float = 35.0
    rear_position_from_axle_mm: float = 45.0
    track_width_mm: float = 105.0
    front_friction_coef: float = 0.05
    rear_friction_coef: float = 0.05


@dataclass
class ChassisParams:
    """
    シャーシ形状パラメータ

    単位:
        wheelbase_mm          : ホイールベース [mm]
        track_width_front_mm  : フロントトレッド幅（タイヤ中心間） [mm]
        track_width_rear_mm   : リアトレッド幅（タイヤ中心間） [mm]
        mass_kg               : シャーシ単体質量 [kg] [仮説値]
        com_height_mm         : 重心高（地面から） [mm] [仮説値]
    """

    chassis_type: str                           # "AR" / "MA" / "MS" / "FM-A" / "VZ" など
    wheelbase_mm: float
    track_width_front_mm: float
    track_width_rear_mm: float
    mass_kg: float = 0.080                      # [仮説値]
    com_height_mm: float = 15.0                 # [仮説値]


@dataclass
class VehicleParams:
    """
    車体パラメータ

    単位:
        mass_kg              : [kg]
        tire_diameter_mm     : [mm]
        gear_ratio           : 無次元（モーター回転数 / タイヤ回転数）
        rolling_resistance_coef : 無次元 [仮説値]
        drivetrain_efficiency : 無次元 [仮説値]
    """

    mass_kg: float
    tire_diameter_mm: float
    gear_ratio: float
    drivetrain_type: Literal["4wd", "2wd"]
    motor: MotorParams
    battery: BatteryParams
    rolling_resistance_coef: float = 0.025
    drivetrain_efficiency: float = 0.85
    tire: Optional[TireParams] = None           # None = 後方互換モード
    roller: Optional[RollerConfig] = None       # None = ローラーなし（タイヤ横力のみ）
    chassis: Optional[ChassisParams] = None     # None = シャーシ形状考慮なし


@dataclass
class SectionParams:
    """
    コース1区間のパラメータ

    単位:
        length_mm  : [mm]
        slope_deg  : [deg]（登り=正、下り=負）
    """

    section_id: int
    section_type: str  # 'straight', 'curve', 'slope_up', 'slope_down', 'lane_change'
    length_mm: float
    slope_deg: float = 0.0
    note: str = ""

    @property
    def length_m(self) -> float:
        """区間長 [m]"""
        return self.length_mm / 1000.0

    @property
    def slope_rad(self) -> float:
        """傾斜角 [rad]"""
        return math.radians(self.slope_deg)


@dataclass
class TrackParams:
    """
    コースパラメータ

    単位:
        corner_radius_mm  : [mm]
        obstacle_height_mm: [mm]
    """

    name: str
    sections: List[SectionParams]
    corner_radius_mm: float
    obstacle_height_mm: float
    obstacle_per_lap: int = 1

    @property
    def lap_length_mm(self) -> float:
        """1周の全長 [mm]"""
        return sum(s.length_mm for s in self.sections)

    @property
    def lap_length_m(self) -> float:
        """1周の全長 [m]"""
        return self.lap_length_mm / 1000.0


@dataclass
class RaceRules:
    """
    レースレギュレーション

    単位:
        time_limit_s              : [s]（10分=600, 20分=1200）
        dnf_speed_threshold_mps   : [m/s]
    """

    time_limit_s: float
    dnf_speed_threshold_mps: float = 0.05
