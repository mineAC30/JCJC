"""
code/plot/lap_plots.py — シミュレーション結果のグラフ生成

生成するグラフ (2×3 サブプロット):
    [0,0] 累積エネルギー消費量      (ラップ × mAh)
    [0,1] ラップタイム推移          (ラップ × 秒)
    [0,2] セクション速度プロファイル  (セクション番号 × m/s, 第1周)
    [1,0] 速度損失の累積推移        (ラップ × 累積 m/s)
    [1,1] 速度損失内訳 (タイプ別)   (水平バー)
    [1,2] スリップ角・ローラー側面力  (曲線セクション, 第1周)
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sim_core.domain.results import RaceResult

import matplotlib
matplotlib.use("Agg")  # GUIなし環境でも動作するバックエンド

import matplotlib.font_manager as fm
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt

# ──────────────────────────────────────────────
# 日本語フォント設定（利用可能なフォントから自動選択）
# ──────────────────────────────────────────────
_JP_FONTS = ["Yu Gothic", "MS Gothic", "Meiryo", "IPAGothic", "Noto Sans CJK JP", "TakaoGothic"]
_jp_font_found = False
for _font_name in _JP_FONTS:
    if any(f.name == _font_name for f in fm.fontManager.ttflist):
        plt.rcParams["font.family"] = _font_name
        _jp_font_found = True
        break

if not _jp_font_found:
    # 日本語フォントが見つからない場合は英語ラベルにフォールバック
    plt.rcParams["font.family"] = "DejaVu Sans"

plt.rcParams.update({
    "axes.titlesize": 10,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 8,
    "figure.facecolor": "white",
    "axes.facecolor": "#f8f8f8",
    "axes.grid": True,
    "grid.alpha": 0.35,
    "grid.linestyle": "--",
})

# ──────────────────────────────────────────────
# セクションタイプ別カラーマップ
# ──────────────────────────────────────────────
_SECTION_COLORS: dict[str, str] = {
    "straight":    "#4a90d9",
    "curve":       "#e67e22",
    "lane_change": "#2ecc71",
    "slope_up":    "#9b59b6",
    "slope_down":  "#1abc9c",
    "obstacle":    "#e74c3c",
}
_DEFAULT_COLOR = "#95a5a6"

# ラベル（日本語フォントなしでも見えるよう和訳付き）
_SECTION_LABELS: dict[str, str] = {
    "straight":    "直線 (straight)",
    "curve":       "曲線 (curve)",
    "lane_change": "レーチェン (lane_change)",
    "slope_up":    "登り坂 (slope_up)",
    "slope_down":  "下り坂 (slope_down)",
    "obstacle":    "障害物 (obstacle)",
}


def _section_color(stype: str) -> str:
    return _SECTION_COLORS.get(stype, _DEFAULT_COLOR)


def _lap1_sections(result: "RaceResult") -> list:
    if not result.lap_results:
        return []
    return result.lap_results[0].section_results


def _no_data(ax: plt.Axes, title: str = "") -> None:
    ax.text(0.5, 0.5, "No data", ha="center", va="center",
            transform=ax.transAxes, color="gray", fontsize=10)
    if title:
        ax.set_title(title)


# ──────────────────────────────────────────────
# 個別グラフ関数
# ──────────────────────────────────────────────

def plot_energy_cumulative(result: "RaceResult", ax: plt.Axes) -> None:
    """[左上] 累積エネルギー消費量の推移"""
    cumulative: list[float] = []
    total = 0.0
    for lap in result.lap_results:
        total += lap.energy_consumed_mAh
        cumulative.append(total)

    if not cumulative:
        return _no_data(ax, "累積エネルギー消費量")

    laps = list(range(1, len(cumulative) + 1))
    ax.plot(laps, cumulative, color="#4a90d9", linewidth=1.5)
    ax.fill_between(laps, cumulative, alpha=0.18, color="#4a90d9")
    ax.set_xlabel("Lap #")
    ax.set_ylabel("Cumulative Energy [mAh]")
    ax.set_title("累積エネルギー消費量")


def plot_lap_times(result: "RaceResult", ax: plt.Axes) -> None:
    """[中央上] ラップタイム推移"""
    times = [lap.time_s for lap in result.lap_results]
    if not times:
        return _no_data(ax, "ラップタイム推移")

    laps = list(range(1, len(times) + 1))
    ax.plot(laps, times, color="#2ecc71", linewidth=0.8, alpha=0.7)
    avg = sum(times) / len(times)
    ax.axhline(avg, color="red", linestyle="--", linewidth=1.2,
               label=f"avg {avg:.4f} s")
    ax.set_xlabel("Lap #")
    ax.set_ylabel("Lap Time [s]")
    ax.set_title("ラップタイム推移")
    ax.legend(loc="upper right")


def plot_speed_profile(result: "RaceResult", ax: plt.Axes) -> None:
    """[右上] セクション速度プロファイル（第1周）"""
    sections = _lap1_sections(result)
    if not sections:
        return _no_data(ax, "速度プロファイル (Lap 1)")

    ids = [s.section_id for s in sections]
    speeds = [s.avg_speed_mps for s in sections]
    colors_bar = [_section_color(s.section_type) for s in sections]
    ax.bar(ids, speeds, color=colors_bar, width=0.7, alpha=0.85)
    ax.set_xlabel("Section #")
    ax.set_ylabel("Avg Speed [m/s]")
    ax.set_title("速度プロファイル (Lap 1)")

    # 凡例（タイプ別）
    handles = []
    seen: set[str] = set()
    for s in sections:
        if s.section_type not in seen:
            label = _SECTION_LABELS.get(s.section_type, s.section_type)
            handles.append(
                plt.Rectangle((0, 0), 1, 1,
                               color=_section_color(s.section_type),
                               label=label)
            )
            seen.add(s.section_type)
    ax.legend(handles=handles, fontsize=7, loc="lower right")


def plot_cumulative_speed_loss(result: "RaceResult", ax: plt.Axes) -> None:
    """[左下] 速度損失の累積推移"""
    cumulative: list[float] = []
    total = 0.0
    for lap in result.lap_results:
        lap_loss = sum(s.speed_loss_mps for s in lap.section_results)
        total += lap_loss
        cumulative.append(total)

    if not cumulative:
        return _no_data(ax, "速度損失累積推移")

    laps = list(range(1, len(cumulative) + 1))
    ax.plot(laps, cumulative, color="#e74c3c", linewidth=1.5)
    ax.fill_between(laps, cumulative, alpha=0.18, color="#e74c3c")
    ax.set_xlabel("Lap #")
    ax.set_ylabel("Cumulative Speed Loss [m/s · lap]")
    ax.set_title("速度損失累積推移")


def plot_speed_loss_breakdown(result: "RaceResult", ax: plt.Axes) -> None:
    """[中央下] 速度損失内訳（セクションタイプ別累積）"""
    from collections import defaultdict

    loss_by_type: dict[str, float] = defaultdict(float)
    for lap in result.lap_results:
        for s in lap.section_results:
            if s.speed_loss_mps > 0:
                loss_by_type[s.section_type] += s.speed_loss_mps

    if not loss_by_type:
        ax.text(0.5, 0.5, "速度損失なし", ha="center", va="center",
                transform=ax.transAxes, color="gray")
        ax.set_title("速度損失内訳 (全周回累積)")
        return

    items = sorted(loss_by_type.items(), key=lambda x: x[1], reverse=True)
    types_list = [_SECTION_LABELS.get(t, t) for t, _ in items]
    values_list = [v for _, v in items]
    colors_bar = [_section_color(t) for t, _ in items]

    ax.barh(types_list, values_list, color=colors_bar, alpha=0.85)
    ax.set_xlabel("Cumulative Speed Loss [m/s]")
    ax.set_title("速度損失内訳 (全周回累積)")


def plot_slip_and_roller(result: "RaceResult", ax: plt.Axes) -> None:
    """[右下] スリップ角・ローラー側面力（第1周の曲線セクション）"""
    sections = _lap1_sections(result)
    curve_secs = [s for s in sections if s.section_type == "curve"]

    if not curve_secs:
        return _no_data(ax, "スリップ角・ローラー側面力 (Lap 1)")

    ids = list(range(1, len(curve_secs) + 1))
    slip_deg = [math.degrees(s.slip_angle_rad) for s in curve_secs]
    roller_n = [s.roller_side_force_N for s in curve_secs]

    color_slip = "#e67e22"
    color_roller = "#9b59b6"

    ax2 = ax.twinx()
    ax.bar(ids, slip_deg, color=color_slip, alpha=0.65,
           label="Slip Angle [°]", width=0.4)
    ax2.plot(ids, roller_n, color=color_roller, marker="o",
             linewidth=1.5, markersize=5, label="Roller Side Force [N]")

    ax.set_xlabel("Curve Section # (Lap 1)")
    ax.set_ylabel("Slip Angle [°]", color=color_slip)
    ax2.set_ylabel("Roller Side Force [N]", color=color_roller)
    ax.set_title("スリップ角・ローラー側面力 (Lap 1)")
    ax.tick_params(axis="y", labelcolor=color_slip)
    ax2.tick_params(axis="y", labelcolor=color_roller)

    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, fontsize=7, loc="upper right")


# ──────────────────────────────────────────────
# メイン: 全グラフを描画・保存
# ──────────────────────────────────────────────

def plot_all(
    result: "RaceResult",
    output_dir: Path,
    title_prefix: str = "",
) -> Path:
    """
    全グラフを 2×3 レイアウトで描画し、PNG として保存する。

    引数:
        result      : RaceResult
        output_dir  : 保存先ディレクトリ（存在しない場合は作成）
        title_prefix: タイトルに追加するプレフィックス（モーター名など）

    戻り値:
        保存した PNG ファイルの Path
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fig = plt.figure(figsize=(18, 11))

    title_main = (
        f"{'[' + title_prefix + ']  ' if title_prefix else ''}"
        f"Simulation Result Summary\n"
        f"Total Laps: {result.total_laps}  /  "
        f"Total Time: {result.total_time_s:.1f} s  /  "
        f"DNF: {'YES' if result.dnf else 'NO'}"
    )
    fig.suptitle(title_main, fontsize=12, fontweight="bold")

    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.48, wspace=0.40)

    ax_energy  = fig.add_subplot(gs[0, 0])
    ax_laptime = fig.add_subplot(gs[0, 1])
    ax_speed   = fig.add_subplot(gs[0, 2])
    ax_loss    = fig.add_subplot(gs[1, 0])
    ax_break   = fig.add_subplot(gs[1, 1])
    ax_slip    = fig.add_subplot(gs[1, 2])

    plot_energy_cumulative(result, ax_energy)
    plot_lap_times(result, ax_laptime)
    plot_speed_profile(result, ax_speed)
    plot_cumulative_speed_loss(result, ax_loss)
    plot_speed_loss_breakdown(result, ax_break)
    plot_slip_and_roller(result, ax_slip)

    out_path = output_dir / "summary_plots.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return out_path
