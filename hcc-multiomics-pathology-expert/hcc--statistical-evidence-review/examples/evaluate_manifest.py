#!/usr/bin/env python3
"""Perform structural HCC manifest checks before inference."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with args.manifest.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    findings: list[dict[str, str]] = []
    identifiers = [row.get("sample_id", "") for row in rows]
    duplicate_ids = [key for key, count in Counter(identifiers).items() if key and count > 1]
    if duplicate_ids:
        findings.append({"status": "fail", "rule": "unique_sample_id", "detail": f"duplicates: {duplicate_ids}"})
    if any(row.get("tissue_role", "").lower() == "healthy_normal" and "adjacent" in row.get("region", "").lower() for row in rows):
        findings.append({"status": "fail", "rule": "adjacent_not_healthy", "detail": "adjacent region labelled healthy_normal"})
    if any(not row.get("patient_id", "").strip() for row in rows):
        findings.append({"status": "fail", "rule": "patient_level_inference", "detail": "at least one row lacks patient_id"})
    if any(row.get("pairing_level", "") in {"", "cross_cohort_reference"} for row in rows):
        findings.append({"status": "warn", "rule": "cross_modal_pairing", "detail": "at least one row lacks local biological pairing"})
    if not findings:
        findings.append({"status": "pass", "rule": "manifest_structure", "detail": "no structural violations detected"})
    result = {"overall": "fail" if any(item["status"] == "fail" for item in findings) else "warn" if any(item["status"] == "warn" for item in findings) else "pass", "findings": findings}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output)
    return 1 if result["overall"] == "fail" else 0


if __name__ == "__main__":
    raise SystemExit(main())
