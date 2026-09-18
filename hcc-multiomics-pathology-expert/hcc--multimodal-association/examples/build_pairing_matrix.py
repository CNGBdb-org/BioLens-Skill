#!/usr/bin/env python3
"""Build a patient-level modality pairing matrix from sample_manifest.tsv."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with args.manifest.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter="\t"))
    by_patient: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row.get("patient_id"):
            by_patient[row["patient_id"]].append(row)
    modalities = sorted({row.get("modality", "") for row in rows if row.get("modality")})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["patient_id", *modalities, "strongest_pairing_level"], delimiter="\t")
        writer.writeheader()
        for patient_id, patient_rows in sorted(by_patient.items()):
            levels = {row.get("pairing_level", "") for row in patient_rows if row.get("pairing_level")}
            writer.writerow({
                "patient_id": patient_id,
                **{modality: sum(row.get("modality") == modality for row in patient_rows) for modality in modalities},
                "strongest_pairing_level": sorted(levels)[0] if len(levels) == 1 else "mixed_or_undocumented",
            })
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
