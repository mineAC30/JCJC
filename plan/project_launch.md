
# Mini4WD Optimization Project - Copilot Instructions

## 目的

このプロジェクトの目的は、ミニ四駆競技において  
**与えられた電池を使い、制限時間内（10分または20分）で周回数を最大化するための物理モデルとシミュレーション基盤をPythonで構築すること** である。

このプロジェクトでは、いきなり最適化アルゴリズムに飛びつかず、まず以下を重視する。

1. 現象理解
2. 物理構造の言語化
3. 計測可能パラメータとの接続
4. Pythonでの拡張可能な実装
5. 後から物理モデルを差し替えられる構造

---

## レギュレーション前提

このプロジェクトで扱う競技条件は以下とする。

- 指定電池を使用する
- 制限時間は **10分または20分**
- コースは **JCJC**
- 1周ごとに **約5mmのゴム段差** が存在する
- 評価指標は **制限時間内の総周回数**

---

## 基本方針

### 1. まず物理構造を定義する
最初から複雑な最適化問題として扱わず、まず対象を物理現象として分解すること。

例:
- 直線区間での加速
- コーナーでの減速または安定性制約
- 段差通過時の速度低下、姿勢乱れ、ロス
- 電池消耗に伴う出力低下
- 駆動形式差分（四駆 / 二駆など）
- 摩擦、転がり抵抗、ギア比、タイヤ径の影響

### 2. 計測可能パラメータを優先する
モデル化する変数は、できる限り実験や既知仕様で与えられるものを優先すること。

例:
- 車体質量
- タイヤ径
- ギア比
- モーター特性の近似値
- 電池電圧または内部抵抗の近似
- 周回タイム
- 段差通過時の速度低下
- コーナーでの失速や飛び出し条件

### 3. 物理式は簡易モデルから始める
最初から正確さを求めすぎず、まずは説明可能な簡易モデルを作ること。
精度向上は段階的に行う。

### 4. モデルは後から変更できるようにする
物理構造や仮説は将来変更される前提で設計すること。
そのため、実装は「固定された正解」ではなく、
**仮説を交換可能な構造** にすること。

### 5. Python実装は構造を表現するための手段
Pythonは数値計算だけでなく、
**物理構造・前提・責務の分離を明示するための言語**
として使うこと。

---

## 実装思想

このプロジェクトでは、以下の思想で実装すること。

### A. 物理モデル中心
コード都合ではなく、物理意味を中心に構造を作る。

悪い例:
- utils.py に何でも詰め込む
- とりあえず1ファイルに全部書く

良い例:
- motor model
- battery model
- drivetrain model
- lap simulation
- obstacle loss model
- scoring / evaluation

のように責務で分割する。

### B. 小さく動くものを優先
最初から全部入りを作らず、まずは
「1周を近似計算できる最小構成」
を作ること。

### C. 仮説をコード化する
各モデルは「真理」ではなく「仮説」である。
よって、式や係数には説明を残し、交換しやすくする。

### D. 入出力を明確にする
各モデルは、入力と出力を明確に持つ純粋関数またはそれに近い形を優先する。

---

## 開発フェーズ

### Phase 1: 言葉で定義する
最初に以下を文章で整理すること。

- 1周とは何か
- 周回数を決める主要因は何か
- エネルギー消費は何で決まるか
- 速度低下イベントは何か
- 完走不能条件は何か
- 二駆と四駆の差は何か

### Phase 2: 最小モデルを作る
最小限として以下を成立させる。

- 車体パラメータを入力できる
- 電池状態を持てる
- 1周の所要時間を推定できる
- 1周でのエネルギー消費を推定できる
- 時間切れまで周回シミュレーションできる

### Phase 3: モデル分解
以下を独立モジュールとして分離する。

- motor
- battery
- drivetrain
- rolling resistance
- obstacle / step loss
- cornering loss
- lap simulator
- race simulator
- evaluator

### Phase 4: 検証可能化
実測と比較できるようにする。

- ログ出力
- 条件保存
- パラメータ設定ファイル
- 実測値との比較
- 感度分析

### Phase 5: 最適化
物理構造がある程度見えた段階でのみ最適化へ進む。

---

## コーディング規約

### 1. dataclass を積極的に使う
パラメータ群や状態量は dataclass で定義すること。

推奨例:
- `VehicleParams`
- `MotorParams`
- `BatteryParams`
- `TrackParams`
- `RaceRules`
- `LapResult`
- `RaceResult`

### 2. 型ヒントを付ける
すべての公開関数に型ヒントをつけること。

### 3. docstring を書く
すべての主要関数・クラスに docstring を付けること。
以下を最低限含める。

- 何を表すか
- 入力
- 出力
- 仮定
- 単位

### 4. 単位を明示する
変数名、コメント、docstring で単位を必ず明示すること。

例:
- speed_mps
- mass_kg
- tire_diameter_mm
- voltage_v
- time_s

### 5. マジックナンバーを避ける
係数や閾値は設定値として外に出すこと。

### 6. Jupyter前提にしすぎない
コアロジックは `.py` に置き、Notebook は検証用途に限定すること。

---

## 推奨ディレクトリ構成

```text
mini4wd_opt/
├─ README.md
├─ pyproject.toml
├─ requirements.txt
├─ configs/
│  ├─ default.yaml
│  ├─ vehicle_example.yaml
│  └─ track_jcjc.yaml
├─ src/
│  └─ mini4wd_opt/
│     ├─ __init__.py
│     ├─ domain/
│     │  ├─ params.py
│     │  ├─ state.py
│     │  └─ results.py
│     ├─ physics/
│     │  ├─ motor.py
│     │  ├─ battery.py
│     │  ├─ drivetrain.py
│     │  ├─ resistance.py
│     │  ├─ obstacle.py
│     │  └─ corner.py
│     ├─ simulation/
│     │  ├─ lap.py
│     │  ├─ race.py
│     │  └─ events.py
│     ├─ evaluation/
│     │  ├─ scorer.py
│     │  └─ sensitivity.py
│     ├─ io/
│     │  ├─ config_loader.py
│     │  └─ logger.py
│     └─ cli/
│        └─ run_simulation.py
├─ tests/
│  ├─ test_motor.py
│  ├─ test_battery.py
│  ├─ test_lap.py
│  └─ test_race.py
└─ notebooks/
   └─ exploration.ipynb