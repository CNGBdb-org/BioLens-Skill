#!/usr/bin/env python3
"""List obs categories (celltype / annotation) with spot counts."""

import argparse
import collections
import json
import sys

from bootstrap import prepare_atlas_paths
from atlas_registry import DEFAULT_OBS_LABEL

prepare_atlas_paths()

from io_core import load_obs_column, sample_name, validate_dataset_dir


def main():
    p = argparse.ArgumentParser(description="List obs categories and spot counts.")
    p.add_argument("data_dir")
    p.add_argument("--by", default=DEFAULT_OBS_LABEL)
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    ds = validate_dataset_dir(args.data_dir)
    labels = load_obs_column(ds, args.by)
    counts = sorted(collections.Counter(labels).items(), key=lambda x: -x[1])
    n_total = len(labels)

    if args.format == "json":
        print(json.dumps({
            "sample": sample_name(ds),
            "column": args.by,
            "categories": [{args.by: k, "n_spots": v, "pct": round(100 * v / n_total, 2)} for k, v in counts],
        }, indent=2, ensure_ascii=False))
        return

    print(f"Sample: {sample_name(ds)}")
    print(f"{args.by} ({len(counts)} categories, {n_total:,} spots):\n")
    print(f"{'n_spots':>10}  {'pct%':>6}  {args.by}")
    for name, n in counts:
        print(f"{n:>10,}  {100 * n / n_total:>6.1f}  {name}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
