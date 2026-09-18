#!/usr/bin/env python3
"""Gene stats by obs column (no plot)."""

import argparse
import sys

from bootstrap import prepare_atlas_paths
from atlas_registry import DEFAULT_OBS_LABEL

prepare_atlas_paths()

from gene_stats_core import print_summary, summarize_gene


def main():
    p = argparse.ArgumentParser(description="Gene expression summary (no plot).")
    p.add_argument("data_dir")
    p.add_argument("-g", "--gene", required=True)
    p.add_argument("--by", default=DEFAULT_OBS_LABEL, help="obs column for grouped stats")
    p.add_argument("--top", type=int, default=0, help="Top N groups by mean (0 = all)")
    p.add_argument(
        "--no-groups",
        action="store_true",
        help="Skip grouped stats (faster; whole-section max/mean only)",
    )
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()
    group = None if args.no_groups else (args.by.strip() or None)
    data = summarize_gene(args.data_dir, args.gene, group_by=group, top_groups=args.top)
    print_summary(data, args.format)


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
