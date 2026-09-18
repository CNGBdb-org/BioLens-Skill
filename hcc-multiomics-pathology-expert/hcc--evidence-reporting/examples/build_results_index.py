#!/usr/bin/env python3
"""Create a small navigable HCC results index from expected artifacts."""

from __future__ import annotations

import argparse
from pathlib import Path


ARTIFACTS = [
    ("数据能力报告", "00_intake/CAPABILITY_REPORT.md"),
    ("分析 manifest", "analysis_manifest.json"),
    ("证据表", "evidence_table.tsv"),
    ("结构化报告", "report.json"),
    ("研究报告", "REPORT.md"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-dir", required=True, type=Path)
    args = parser.parse_args()
    lines = ["# HCC 分析结果索引", "", "仅用于科研分析，需领域专家复核；不用于临床诊断或治疗决策。", "", "## 产物", ""]
    for label, relative in ARTIFACTS:
        state = "可用" if (args.task_dir / relative).exists() else "未生成"
        lines.append(f"- {label}: `{relative}`（{state}）")
    lines.extend(["", "## 结论阅读顺序", "", "1. 先读数据能力报告和配对等级。", "2. 再读研究报告中的统计单位、证据与限制。", "3. 使用证据表和病理坐标回溯关键结论。", ""])
    output = args.task_dir / "RESULTS_INDEX.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
