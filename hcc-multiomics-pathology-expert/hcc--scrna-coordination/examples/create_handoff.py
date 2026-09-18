#!/usr/bin/env python3
"""Create a self-contained DCS handoff request for scrna-seq-expert."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--objective", required=True)
    parser.add_argument("--species", default="Homo sapiens")
    parser.add_argument("--skills", default="single-cell--data-io,single-cell--preprocessing,single-cell--clustering,single-cell--cell-annotation")
    args = parser.parse_args()
    payload = {
        "target_expert": "scrna-seq-expert",
        "target_skills": [item.strip() for item in args.skills.split(",") if item.strip()],
        "objective": args.objective,
        "input_paths": [str(args.input)],
        "input_contract": {"species": args.species, "required_metadata": ["sample_id", "patient_id"], "preserve_raw_counts": True},
        "expected_outputs": {"processed_object": "h5ad_or_rds", "required_obs_columns": ["cell_type", "sample_id", "patient_id", "annotation_confidence"], "required_evidence": ["marker_support", "method_versions"]},
        "return_contract": "Return paths and a structured annotation summary; do not claim HCC-specific malignancy from generic annotation alone.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
