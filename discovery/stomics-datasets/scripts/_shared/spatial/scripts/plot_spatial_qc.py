#!/usr/bin/env python3
"""Spatial QC plot for numeric obs columns."""

import argparse
import sys

import numpy as np

from bootstrap import prepare_atlas_paths

prepare_atlas_paths()

from io_core import load_obs_column, load_schema, load_spatial_xy, sample_name, setup_matplotlib, validate_dataset_dir
from spatial_plot_utils import auto_point_size

QC_DEFAULTS = ["total_counts", "n_genes_by_counts", "pct_counts_mt", "log1p_total_counts"]


def main():
    p = argparse.ArgumentParser(description="Spatial QC metric plot.")
    p.add_argument("data_dir")
    p.add_argument("--metric", "-m", default="total_counts")
    p.add_argument("-o", "--output", default=None)
    p.add_argument("--dpi", type=int, default=120)
    p.add_argument("--fast", action="store_true")
    p.add_argument("--percentile", type=float, default=99.0)
    p.add_argument("--cmap", default="plasma")
    p.add_argument("--list-metrics", action="store_true")
    p.add_argument("--no-cache", action="store_true")
    args = p.parse_args()

    ds = validate_dataset_dir(args.data_dir)
    if args.list_metrics:
        s = load_schema(ds)
        print("Numeric obs:", ", ".join(s.get("obs", [])))
        return

    rel = f"obs/{args.metric}.parquet"
    if not ds.exists(rel):
        print(f"Metric not found: {rel}", file=sys.stderr)
        print(f"Try: {', '.join(QC_DEFAULTS)}", file=sys.stderr)
        sys.exit(1)

    title = sample_name(ds)
    out = args.output or os.path.join(ds.output_dir(), f"spatial_qc_{args.metric}.png")

    xy = load_spatial_xy(ds, use_cache=not args.no_cache)
    vals = load_obs_column(ds, args.metric).astype(np.float64)
    x, y = xy[:, 0], xy[:, 1]

    vmax = float(np.percentile(vals, args.percentile))
    vmin = float(np.min(vals))

    n = len(vals)
    plt = setup_matplotlib()
    dpi = 120 if args.fast else args.dpi
    fig, ax = plt.subplots(figsize=(8, 6.5) if args.fast else (10, 8), dpi=dpi)
    sc = ax.scatter(x, y, c=vals, cmap=args.cmap, s=auto_point_size(n, x=x, y=y, fast=args.fast), linewidths=0, rasterized=True, vmin=vmin, vmax=vmax, alpha=1.0)
    ax.set_aspect("equal")
    ax.set_title(f"{title} — {args.metric} (n={len(vals):,})")
    fig.colorbar(sc, ax=ax, shrink=0.7).set_label(f"{args.metric} (vmax p{args.percentile:g})")
    import matplotlib.pyplot as plt_module
    plt_module.tight_layout()
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    import os
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
