"""
code/plot/save_run.py — シミュレーション結果の数値データ保存

保存内容:
    section_data.csv  : 全セクション詳細データ（スリップ角・損失なども含む）
    lap_summary.csv   : ラップごとのサマリー
    configs/          : 演算で使用した YAML 設定ファイルのコピー
"""

from __future__ import annotations

import csv
import math
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sim_core.domain.results import RaceResult


def save_section_csv(result: "RaceResult", output_dir: Path) -> Path:
    """全セクションデータを CSV に保存する。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "section_data.csv"

    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "lap",
            "section_id",
            "section_type",
            "time_s",
            "energy_mAh",
            "avg_speed_mps",
            "speed_loss_mps",
            "slip_angle_deg",
            "roller_side_force_N",
        ])
        for lap in result.lap_results:
            for s in lap.section_results:
                writer.writerow([
                    lap.lap_number,
                    s.section_id,
                    s.section_type,
                    f"{s.time_s:.6f}",
                    f"{s.energy_consumed_mAh:.5f}",
                    f"{s.avg_speed_mps:.4f}",
                    f"{s.speed_loss_mps:.4f}",
                    f"{math.degrees(s.slip_angle_rad):.4f}",
                    f"{s.roller_side_force_N:.4f}",
                ])
    return out_path


def save_lap_csv(result: "RaceResult", output_dir: Path) -> Path:
    """ラップサマリー CSV を保存する。"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "lap_summary.csv"

    with open(out_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow([
            "lap",
            "time_s",
            "energy_mAh",
            "avg_speed_mps",
            "total_speed_loss_mps",
            "max_slip_angle_deg",
            "max_roller_side_force_N",
        ])
        for lap in result.lap_results:
            total_loss = sum(s.speed_loss_mps for s in lap.section_results)
            max_slip = max(
                (math.degrees(s.slip_angle_rad) for s in lap.section_results),
                default=0.0,
            )
            max_roller = max(
                (s.roller_side_force_N for s in lap.section_results),
                default=0.0,
            )
            writer.writerow([
                lap.lap_number,
                f"{lap.time_s:.6f}",
                f"{lap.energy_consumed_mAh:.5f}",
                f"{lap.avg_speed_mps:.4f}",
                f"{total_loss:.4f}",
                f"{max_slip:.4f}",
                f"{max_roller:.4f}",
            ])
    return out_path


def save_configs(yaml_paths: dict[str, Path], output_dir: Path) -> Path:
    """使用した設定 YAML を output_dir/configs/ にコピーする。"""
    config_dir = Path(output_dir) / "configs"
    config_dir.mkdir(parents=True, exist_ok=True)
    for src_path in yaml_paths.values():
        src = Path(src_path)
        if src.exists():
            shutil.copy2(src, config_dir / src.name)
    return config_dir


def save_all(
    result: "RaceResult",
    output_dir: Path,
    yaml_paths: dict[str, Path] | None = None,
) -> dict[str, Path]:
    """
    数値データを一括保存する。

    引数:
        result      : RaceResult
        output_dir  : 保存先ディレクトリ
        yaml_paths  : コピーする YAML ファイル辞書 {"vehicle": Path, ...}

    戻り値:
        {"section_csv": Path, "lap_csv": Path, "config_dir": Path | None}
    """
    section_path = save_section_csv(result, output_dir)
    lap_path = save_lap_csv(result, output_dir)
    config_dir = None
    if yaml_paths:
        config_dir = save_configs(yaml_paths, output_dir)

    return {
        "section_csv": section_path,
        "lap_csv": lap_path,
        "config_dir": config_dir,
    }
