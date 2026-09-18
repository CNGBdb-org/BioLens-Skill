#!/usr/bin/env python3
"""Validate a coordinate manifest before retrieving pathology evidence patches."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


REQUIRED = {"slide_id", "x", "y", "level_or_mpp", "patch_size", "selection_reason"}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coordinates", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with args.coordinates.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"missing columns: {sorted(missing)}")
        rows = list(reader)
    invalid: list[str] = []
    seen: set[tuple[str, str, str, str]] = set()
    for index, row in enumerate(rows, start=2):
        try:
            x, y, size = float(row["x"]), float(row["y"]), float(row["patch_size"])
            if min(x, y) < 0 or size <= 0:
                invalid.append(f"line {index}: negative coordinate or non-positive patch_size")
        except ValueError:
            invalid.append(f"line {index}: x/y/patch_size must be numeric")
            continue
        key = (row["slide_id"], row["x"], row["y"], row["level_or_mpp"])
        if key in seen:
            invalid.append(f"line {index}: duplicate patch coordinate")
        seen.add(key)
    result = {"status": "fail" if invalid else "pass", "coordinate_count": len(rows), "issues": invalid}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output)
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
