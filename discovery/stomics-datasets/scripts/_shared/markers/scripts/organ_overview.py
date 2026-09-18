#!/usr/bin/env python3
"""Obs group composition table + bar chart."""

import argparse
import collections
import json
import os
import sys

from bootstrap import prepare_atlas_paths
from atlas_registry import DEFAULT_OBS_LABEL

prepare_atlas_paths()

from io_core import load_obs_column, sample_name, setup_matplotlib, validate_dataset_dir


def main():
    p = argparse.ArgumentParser(description="Composition table + bar chart.")
    p.add_argument("data_dir")
    p.add_argument("--by", default=DEFAULT_OBS_LABEL)
    p.add_argument("--top", type=int, default=0)
    p.add_argument("-o", "--output", default=None)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--no-plot", action="store_true")
    args = p.parse_args()

    ds = validate_dataset_dir(args.data_dir)
    labels = load_obs_column(ds, args.by)
    counts = sorted(collections.Counter(labels).items(), key=lambda x: -x[1])
    n_total = len(labels)
    if args.top > 0:
        counts = counts[: args.top]

    rows = [{args.by: k, "n_spots": v, "pct": round(100 * v / n_total, 2)} for k, v in counts]

    if args.format == "json":
        print(json.dumps({"sample": sample_name(ds), "total_spots": n_total, "categories": rows}, indent=2, ensure_ascii=False))
    else:
        print(f"Sample: {sample_name(ds)} — {n_total:,} spots, {len(counts)} categories shown\n")
        print(f"{'n_spots':>10}  {'pct%':>6}  {args.by}")
        for row in rows:
            print(f"{row['n_spots']:>10,}  {row['pct']:>6.1f}  {row[args.by]}")

    if args.no_plot:
        return

    out = args.output or os.path.join(ds.output_dir(), f"organ_overview_{args.by}.png")
    names = [r[args.by] for r in rows][::-1]
    vals = [r["n_spots"] for r in rows][::-1]

    plt = setup_matplotlib()
    fig, ax = plt.subplots(figsize=(8, max(4, 0.25 * len(names))))
    ax.barh(range(len(names)), vals, color="#4DBBD5")
    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=7)
    ax.set_xlabel("spot count")
    ax.set_title(f"{sample_name(ds)} — {args.by} composition")
    import matplotlib.pyplot as plt_module
    plt_module.tight_layout()
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
