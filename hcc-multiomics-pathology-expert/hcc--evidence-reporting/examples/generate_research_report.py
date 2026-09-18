#!/usr/bin/env python3
"""Generate a compact research-use HCC report from structured run artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def optional_json(path: Path | None) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path and path.exists() else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", required=True, type=Path)
    parser.add_argument("--evidence-synthesis", type=Path)
    parser.add_argument("--manifest-evaluation", type=Path)
    args = parser.parse_args()

    args.task_dir.mkdir(parents=True, exist_ok=True)
    evidence = optional_json(args.evidence_synthesis)
    manifest = optional_json(args.manifest_evaluation)
    status = manifest.get("status", "not_reviewed") if manifest else "not_reviewed"
    limitations = (evidence or {}).get("limitations", ["No structured evidence synthesis was supplied."])
    report = {
        "research_use_only": True,
        "statistical_review_status": status,
        "available_modalities": (evidence or {}).get("available_modalities", []),
        "evidence": {key: (evidence or {}).get(key) for key in ("spatial", "pathology", "bulk")},
        "limitations": limitations,
        "release_rule": "Do not make a definite HCC biological conclusion when statistical_review_status is fail or not_reviewed.",
    }
    (args.task_dir / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# HCC 多组学病理研究报告",
        "",
        "**仅用于科研分析，需领域专家复核；不用于临床诊断或治疗决策。**",
        "",
        "## 审查状态",
        "",
        f"- 统计/证据审查：`{status}`",
        f"- 已纳入模态：{', '.join(report['available_modalities']) or '未提供'}",
        "",
        "## 已有证据",
        "",
    ]
    for name in ("spatial", "pathology", "bulk"):
        payload = report["evidence"].get(name)
        lines.append(f"- {name}: `{json.dumps(payload, ensure_ascii=False) if payload else '未提供'}`")
    lines.extend(["", "## 限制与不能推出的结论", ""])
    lines.extend(f"- {item}" for item in limitations)
    lines.extend(["", "## 交付规则", "", f"- {report['release_rule']}", ""])
    (args.task_dir / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(args.task_dir / "REPORT.md")


if __name__ == "__main__":
    main()
