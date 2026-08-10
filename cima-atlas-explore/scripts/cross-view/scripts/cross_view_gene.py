#!/usr/bin/env python3
"""Compare one gene across CIMA lineage views (PBMCs, CD4T, B, …)."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from bootstrap import prepare_atlas_paths

prepare_atlas_paths()

from cima_constants import CIMA_VIEWS, VIEW_STEMS
from gene_stats_core import summarize_gene
from io_core import setup_matplotlib


def main():
    p = argparse.ArgumentParser(description="Compare gene expression across CIMA views.")
    p.add_argument("-g", "--gene", required=True)
    p.add_argument("--views", "-V", default=",".join(VIEW_STEMS), help="Comma-separated stems")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--plot", action="store_true")
    p.add_argument("-o", "--output", default=None)
    args = p.parse_args()

    stems = [x.strip() for x in args.views.split(",") if x.strip()]
    label_map = {v["stem"]: v["label"] for v in CIMA_VIEWS}
    rows = []
    t0 = time.perf_counter()
    for stem in stems:
        try:
            s = summarize_gene(stem, args.gene)
            rows.append({
                "view": stem,
                "label": label_map.get(stem, stem),
                "n_cells": s["n_spots"],
                "pct_expressing": s["pct_expressing"],
                "mean_all": s["mean_all_spots"],
                "mean_expr": s["mean_expressing"],
            })
        except (FileNotFoundError, OSError, Exception) as e:
            rows.append({"view": stem, "error": str(e)})

    rows.sort(key=lambda r: r.get("mean_all", -1), reverse=True)

    if args.format == "json":
        print(json.dumps({"gene": args.gene, "views": rows}, indent=2, ensure_ascii=False))
        return

    print(f"Gene: {args.gene}  ({time.perf_counter() - t0:.1f}s)\n")
    print(f"{'view':<10} {'n_cells':>12} {'pct%':>8} {'mean_all':>10} {'mean_expr':>10}")
    for r in rows:
        if "error" in r:
            print(f"{r['view']:<10} ERROR: {r['error']}")
            continue
        print(
            f"{r['view']:<10} {r['n_cells']:>12,} {r['pct_expressing']:>8.1f} "
            f"{r['mean_all']:>10.4f} {r['mean_expr']:>10.4f}"
        )

    if args.plot:
        ok = [r for r in rows if "error" not in r]
        if not ok:
            return
        labels = [r["view"] for r in ok]
        vals = [r["mean_all"] for r in ok]
        out = args.output or os.path.join(os.getcwd(), f"cross_view_{args.gene}.png")
        plt = setup_matplotlib()
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(labels, vals, color="#00A087")
        ax.set_ylabel("Mean expression (all cells)")
        ax.set_title(f"CIMA cross-view: {args.gene}")
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
