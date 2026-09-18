#!/usr/bin/env python3
"""Gene stats by default obs column + spatial plot."""

import argparse
import os
import sys

from bootstrap import prepare_atlas_paths, shared_root
from atlas_registry import DEFAULT_OBS_LABEL

prepare_atlas_paths()
sys.path.insert(0, os.path.join(shared_root(), "spatial", "scripts"))

from gene_stats_core import print_summary, summarize_gene
from plot_spatial_gene import plot_gene


def main():
    p = argparse.ArgumentParser(description="Gene expression: summary + spatial PNG.")
    p.add_argument("data_dir")
    p.add_argument("-g", "--gene", required=True)
    p.add_argument("--by", default=DEFAULT_OBS_LABEL)
    p.add_argument("--top", type=int, default=8)
    p.add_argument("--no-plot", action="store_true")
    p.add_argument("--no-summary", action="store_true")
    p.add_argument("-o", "--output", default=None)
    p.add_argument("--fast", action="store_true")
    p.add_argument("--dpi", type=int, default=120)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--vmin", type=float, default=None)
    p.add_argument("--vmax", type=float, default=None)
    args = p.parse_args()

    if not args.no_summary:
        data = summarize_gene(args.data_dir, args.gene, group_by=args.by, top_groups=args.top)
        print_summary(data, args.format)

    if not args.no_plot:
        if args.format == "json" and not args.no_summary:
            print("", file=sys.stderr)
        plot_gene(
            args.data_dir, args.gene, args.output,
            fast=args.fast, dpi=args.dpi,
            vmin=args.vmin, vmax=args.vmax,
        )


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
