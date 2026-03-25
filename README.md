# Mini4WD Optimization Project

## 目的

JCJC コース上で、**指定電池を使い制限時間（10分 / 20分）内の総周回数を最大化** するための  
物理モデルとシミュレーション基盤を Python で構築するプロジェクト。

---

## ディレクトリ構成

```
JCJC/
├── sim-core.py              # トップレベル実行スクリプト（Public API + CLI）
├── sim_core/                # シミュレーションコアパッケージ
│   ├── domain/              # データクラス (VehicleParams, TireParams, RollerConfig, ChassisParams, ...)
│   ├── physics/             # 物理モデル (motor, battery, drivetrain, tire, ...)
│   ├── simulation/          # ラップ・レースシミュレータ
│   ├── evaluation/          # スコア計算・感度分析
│   └── io/                  # YAML/CSV 設定ローダー・ロガー
├── code/
│   └── py/
│       ├── run_simulation.py  # 実行スクリプト（argparse CLI）
│       └── xlsx_to_csv.py     # Excel → CSV 変換ユーティリティ
├── configs/
│   ├── default.yaml           # シミュレーション共通設定
│   ├── track_jcjc.yaml        # JCJCコース定義（data/course.csv 参照）
│   └── vehicle_example.yaml   # 車体設定（tire / roller / chassis セクション含む）
├── data/
│   ├── course.csv             # JCJCコースセクション定義（マスタデータ）
│   └── runs.csv               # 実測走行ログ
├── model-data/
│   ├── motor/
│   │   ├── Summary.csv        # 全モーター仕様一覧
│   │   └── *.csv              # モーター別詳細データ
│   ├── tire/
│   │   └── tire_catalog.csv   # タイヤカタログ（径・幅・材質・摩擦係数 等）
│   ├── roller/
│   │   └── roller_catalog.csv # ローラーカタログ（径・材質・摩擦係数）
│   └── chassis/
│       └── chassis_catalog.csv # シャーシカタログ（ホイールベース・重心高 等）
├── notebooks/
│   └── energy_analysis.ipynb  # バッテリーエネルギー分析
├── plan/
│   └── project_launch.md      # プロジェクト設計方針
└── tests/                     # pytest テスト（37件）
```

---

## クイックスタート

```bash
# 依存関係インストール
pip install -e .

# シミュレーション実行（デフォルト設定）
python sim-core.py

# オプション指定
python sim-core.py \
  --vehicle configs/vehicle_example.yaml \
  --track   configs/track_jcjc.yaml \
  --config  configs/default.yaml \
  --time    600 \
  --verbose

# code/py スクリプトからも実行可能
python code/py/run_simulation.py --time 600
```

---

## コース設定

コースデータは CSV ファイルに保持し、YAML でどの列を読むか指定します。

**`data/course.csv`** （マスタデータ）
```
section,type,length_mm,slope_deg,note
1,straight,200,0,start
...
```

**`configs/track_jcjc.yaml`**
```yaml
track:
  name: "JCJC"
  sections_csv: "../data/course.csv"
  column_map:
    section_id:   "section"
    section_type: "type"
    length_mm:    "length_mm"
    slope_deg:    "slope_deg"
    note:         "note"
```

新しいコースを追加するには、`data/` に CSV を置き、`configs/track_*.yaml` を作成するだけです。

---

## 車体設定

`configs/vehicle_example.yaml` に motor / battery / tire / roller / chassis の 5 セクションを定義します。

### モーター

`motor.name` を `model-data/motor/Summary.csv` の `MotorName` 列と一致する名前に変更するだけで別モーターを選択できます。

```yaml
motor:
  csv:  "../model-data/motor/Summary.csv"
  name: "Atomic-Tuned 2 PRO"
```

### タイヤ

`model-data/tire/tire_catalog.csv` を参照して値を設定します。

```yaml
tire:
  name: "大径ローハイトタイヤ (ミディアム)"
  diameter_mm: 26.0
  width_mm: 12.0
  material: "medium"              # hard / medium / soft / sponge / super_hard
  friction_coef: 0.80             # 横方向摩擦係数（コーナー速度上限に影響）[仮説値]
  rolling_resistance_coef: 0.025  # 転がり抵抗係数 [仮説値]
  cornering_stiffness_N_per_rad: 8.0  # スリップ角計算に使用 [仮説値]
```

`tire` セクションがある場合、コーナーの最大速度はタイヤ摩擦係数により決定されます。  
`tire` を省略すると `configs/default.yaml` の `corner_friction_coefficient` にフォールバックします。

### ローラー

```yaml
roller:
  front_diameter_mm: 13.0
  rear_diameter_mm: 19.0
  front_friction_coef: 0.05   # ローラーとガイドレール間の摩擦係数 [仮説値]
  rear_friction_coef: 0.05
```

`roller` セクションがある場合、タイヤ横力限界を超えた遠心力をローラーが補助し、  
ローラー摩擦による走行抵抗増加をコーナー区間の速度計算に反映します。  
`roller` を省略するとタイヤ横力のみで速度上限を設定します。

### シャーシ

```yaml
chassis:
  chassis_type: "AR"
  wheelbase_mm: 76.5
  track_width_front_mm: 90.0
  track_width_rear_mm: 92.0
  mass_kg: 0.080        # シャーシ単体質量 [仮説値]
  com_height_mm: 15.0   # 重心高 [仮説値]
```

現在は設定値として保持し、将来の横転・重心移動モデルで参照します。

---

## 物理モデル概要

| モジュール | 計算内容 |
|---|---|
| `physics/motor.py` | 端子電圧・トルクから回転数・電流を算出（線形モデル） |
| `physics/drivetrain.py` | ギア比・タイヤ径から車体速度に変換 |
| `physics/battery.py` | SOC・放電曲線・内部抵抗から端子電圧・消費 mAh を算出 |
| `physics/resistance.py` | 転がり抵抗 + 傾斜重力成分 |
| `physics/tire.py` | **スリップ角・横力・ローラー側面力・ローラー摩擦ドラグを算出** |
| `physics/corner.py` | タイヤ摩擦またはローラーなしモードの最大コーナー速度 |
| `physics/obstacle.py` | ゴム段差による速度低下 |

### コーナー計算の分岐

```
tire + roller あり  → ローラーで横力を補助、ローラー摩擦を走行抵抗に加算
                       SectionResult に slip_angle_rad, roller_side_force_N を記録
tire のみ          → タイヤ friction_coef で v_max を設定、スリップ角を記録
両方なし（後方互換）→ default.yaml の corner_friction_coefficient で v_max を設定
```

---

## 開発フェーズ

| フェーズ | 内容 | 状態 |
|---------|------|------|
| Phase 1 | 物理構造の言語化 | ✅ 完了 |
| Phase 2 | 最小モデル実装（1周シミュレーション） | ✅ 完了 |
| Phase 3 | モジュール分解（motor / battery / lap / race） | ✅ 完了 |
| Phase 4 | 検証可能化（ログ・設定ファイル・実測比較・タイヤ/ローラー/シャーシ拡張） | 🔄 進行中 |
| Phase 5 | 最適化 | ⬜ 未着手 |

---

## テスト

```bash
pytest tests/ -v
# 37 passed
```
