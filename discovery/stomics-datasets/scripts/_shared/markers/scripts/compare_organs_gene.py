#!/usr/bin/env python3
"""Compare one gene across selected tissue / annotation groups."""

import argparse
import json
import sys

from bootstrap import prepare_atlas_paths
from atlas_registry import DEFAULT_OBS_LABEL

prepare_atlas_paths()

from gene_stats_core import summarize_gene


def main():
    p = argparse.ArgumentParser(description="Compare gene expression across groups.")
    p.add_argument("data_dir")
    p.add_argument("-g", "--gene", required=True)
    p.add_argument("--organs", "-O", required=True, help="Comma-separated groups, e.g. Liver,Lung,Brain")
    p.add_argument("--by", default=DEFAULT_OBS_LABEL)
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    organs = [x.strip() for x in args.organs.split(",") if x.strip()]
    data = summarize_gene(args.data_dir, args.gene, group_by=args.by, filter_groups=organs, top_groups=0)
    groups = data.get("by_" + args.by, [])
    groups.sort(key=lambda x: x["mean_expression"], reverse=True)
    data["by_" + args.by] = groups

    if args.format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    print(f"Sample: {data['sample']}")
    print(f"Gene:   {data['gene']} — comparing {len(organs)} groups\n")
    print(f"{args.by:<24} {'n_spots':>10} {'pct%':>8} {'mean':>10}")
    for row in groups:
        print(
            f"{row[args.by]:<24} {row['n_spots']:>10,} "
            f"{row['pct_expressing']:>8.1f} {row['mean_expression']:>10.4f}"
        )
    missing = set(organs) - {row[args.by] for row in groups}
    if missing:
        print(f"\nNot found in sample: {', '.join(sorted(missing))}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
