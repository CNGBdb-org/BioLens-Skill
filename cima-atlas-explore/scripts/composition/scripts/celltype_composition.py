#!/usr/bin/env python3
"""Cell-type composition for a CIMA view (l1–l4 hierarchy)."""

from __future__ import annotations

import argparse
import collections
import json
import os
import sys

from bootstrap import prepare_atlas_paths

prepare_atlas_paths()

from cima_constants import CELLTYPE_LEVELS, DEFAULT_VIEW
from io_core import load_obs_column, sample_name, setup_matplotlib, validate_dataset_dir


def composition(data_dir: str, level: str) -> tuple[str, list[dict], int]:
    ds = validate_dataset_dir(data_dir)
    labels = load_obs_column(ds, level)
    ctr = collections.Counter(str(x) for x in labels)
    n = sum(ctr.values())
    rows = [
        {level: k, "n_cells": v, "pct": round(100 * v / n, 2)}
        for k, v in ctr.most_common()
    ]
    return sample_name(ds), rows, n


def main():
    p = argparse.ArgumentParser(description="CIMA cell-type composition.")
    p.add_argument("view", nargs="?", default=DEFAULT_VIEW)
    p.add_argument("--level", "-l", choices=CELLTYPE_LEVELS, default="cell_type_l4")
    p.add_argument("--top", type=int, default=0, help="Show top N types (0 = all)")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--plot", action="store_true")
    p.add_argument("-o", "--output", default=None)
    args = p.parse_args()

    name, rows, n_total = composition(args.view, args.level)
    if args.top > 0:
        rows = rows[: args.top]

    if args.format == "json":
        print(json.dumps({"view": name, "level": args.level, "n_cells": n_total, "types": rows}, indent=2, ensure_ascii=False))
        return

    print(f"View: {name}  |  {args.level}  |  {n_total:,} cells  |  {len(rows)} types\n")
    print(f"{'n_cells':>12}  {'pct%':>7}  {args.level}")
    for row in rows:
        print(f"{row['n_cells']:>12,}  {row['pct']:>7.2f}  {row[args.level]}")

    if args.plot:
        show = rows[:20] if len(rows) > 20 else rows
        labels = [r[args.level] for r in show]
        vals = [r["pct"] for r in show]
        out = args.output or os.path.join(os.getcwd(), args.view, f"composition_{args.level}.png")
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        plt = setup_matplotlib()
        fig, ax = plt.subplots(figsize=(10, max(4, 0.25 * len(show))))
        y = range(len(show))
        ax.barh(list(y), vals, color="#E64B35")
        ax.set_yticks(list(y))
        ax.set_yticklabels(labels, fontsize=7)
        ax.invert_yaxis()
        ax.set_xlabel("Cell fraction (%)")
        ax.set_title(f"CIMA {name} — top {len(show)} {args.level}")
        import matplotlib.pyplot as mp

        mp.tight_layout()
        fig.savefig(out, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"\nSaved: {out}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
