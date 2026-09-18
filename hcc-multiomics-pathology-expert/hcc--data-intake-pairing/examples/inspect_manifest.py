#!/usr/bin/env python3
"""Create an HCC capability plan from a tab-separated sample manifest."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


REQUIRED = {"patient_id", "sample_id", "modality", "disease", "tissue_role", "input_path"}
PAIRING_LEVELS = {
    "same_section", "same_block", "same_specimen", "same_patient_same_timepoint",
    "same_patient_other_timepoint", "cross_cohort_reference",
}


def load_manifest(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        if not reader.fieldnames:
            raise ValueError("manifest has no header")
        missing = REQUIRED - set(reader.fieldnames)
        if missing:
            raise ValueError(f"missing required columns: {', '.join(sorted(missing))}")
        return [{key: (value or "").strip() for key, value in row.items()} for row in reader]


def build_plan(rows: list[dict[str, str]]) -> dict[str, object]:
    warnings: list[str] = []
    blocked: list[str] = []
    diseases = {row["disease"].upper() for row in rows}
    if diseases != {"HCC"}:
        blocked.append(f"HCC-only Expert received disease values: {sorted(diseases)}")
    patient_ids = [row["patient_id"] for row in rows]
    if any(not value for value in patient_ids):
        blocked.append("missing patient_id")
    if any(row["tissue_role"].lower() == "healthy_normal" and "adjacent" in row.get("region", "").lower() for row in rows):
        blocked.append("adjacent sample is labelled healthy_normal")
    for row in rows:
        level = row.get("pairing_level", "")
        if level and level not in PAIRING_LEVELS:
            blocked.append(f"invalid pairing_level for sample {row['sample_id']}: {level}")
    modalities = Counter(row["modality"].lower() for row in rows)
    statuses: dict[str, str] = {
        "data_intake": "blocked" if blocked else "ready",
        "pathology_qc": "ready" if any(key in modalities for key in ("wsi", "he", "pathology")) else "blocked",
        "spatial_tme": "ready" if any("spatial" in key or key in {"visium", "stereo-seq"} for key in modalities) else "blocked",
        "scrna_handoff": "requires_handoff" if any(key in modalities for key in ("scrna", "single_cell", "h5ad")) else "blocked",
        "bulk_pathway": "ready" if any(key in modalities for key in ("bulk_rna", "rna", "rnaseq")) else "blocked",
    }
    if statuses["pathology_qc"] == "ready" and not any(row.get("slide_id") for row in rows):
        warnings.append("pathology input has no slide_id; coordinate evidence cannot be linked reliably")
    if any(row.get("pairing_level", "") in {"", "cross_cohort_reference"} for row in rows):
        warnings.append("at least one modality lacks local biological pairing; restrict cross-modal inference")
    return {
        "status": "blocked" if blocked else "inspected",
        "patient_count": len(set(patient_ids)),
        "sample_count": len(rows),
        "modalities": dict(sorted(modalities.items())),
        "capabilities": statuses,
        "warnings": sorted(set(warnings)),
        "blocked_reasons": sorted(set(blocked)),
    }


def render_report(plan: dict[str, object]) -> str:
    lines = ["# HCC 数据识别与能力报告", "", f"- 状态：{plan['status']}", f"- 患者数：{plan['patient_count']}", f"- 样本数：{plan['sample_count']}", "", "## 模态", ""]
    lines.extend(f"- {name}: {count}" for name, count in dict(plan["modalities"]).items())
    lines.extend(["", "## 能力", ""])
    lines.extend(f"- {name}: {status}" for name, status in dict(plan["capabilities"]).items())
    if plan["warnings"]:
        lines.extend(["", "## 限制", ""] + [f"- {item}" for item in plan["warnings"]])
    if plan["blocked_reasons"]:
        lines.extend(["", "## 阻断原因", ""] + [f"- {item}" for item in plan["blocked_reasons"]])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    rows = load_manifest(args.manifest)
    plan = build_plan(rows)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "capability_plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (args.output / "CAPABILITY_REPORT.md").write_text(render_report(plan), encoding="utf-8")
    print(args.output / "capability_plan.json")
    return 0 if plan["status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
