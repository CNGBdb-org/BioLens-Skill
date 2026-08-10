#!/usr/bin/env python3
"""Major lineage composition across CIMA views."""

from __future__ import annotations

import argparse
import collections
import json
import os
import sys

import numpy as np

from bootstrap import prepare_atlas_paths

prepare_atlas_paths()

from cima_constants import CIMA_VIEWS
from io_core import load_obs_column, setup_matplotlib, validate_dataset_dir


def main():
    p = argparse.ArgumentParser(description="Cell-type landscape across CIMA views.")
    p.add_argument("--level", "-l", default="cell_type_l1")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--plot", action="store_true")
    p.add_argument("-o", "--output", default=None)
    args = p.parse_args()

    view_data = []
    all_types: set[str] = set()
    for v in CIMA_VIEWS:
        try:
            ds = validate_dataset_dir(v["stem"])
            labels = load_obs_column(ds, args.level)
            ctr = collections.Counter(str(x) for x in labels)
            total = sum(ctr.values())
            view_data.append({"stem": v["stem"], "label": v["label"], "total": total, "ctr": ctr})
            all_types.update(ctr.keys())
        except FileNotFoundError as e:
            print(f"Skip {v['stem']}: {e}", file=sys.stderr)

    types = sorted(all_types, key=str)

    if args.format == "json":
        out = []
        for vd in view_data:
            total = vd["total"] or 1
            out.append({
                "view": vd["stem"],
                "n_cells": vd["total"],
                "types": {t: round(100 * vd["ctr"].get(t, 0) / total, 2) for t in types},
            })
        print(json.dumps({"level": args.level, "views": out}, indent=2, ensure_ascii=False))
        return

    print(f"Landscape — {args.level} across {len(view_data)} views\n")
    top = types[:10]
    print(f"{'view':<10}" + "".join(f"{t[:10]:>12}" for t in top))
    for vd in view_data:
        total = vd["total"] or 1
        line = f"{vd['stem']:<10}"
        for t in top:
            line += f"{100 * vd['ctr'].get(t, 0) / total:>12.1f}"
        print(line)

    if args.plot:
        stems = [vd["stem"] for vd in view_data]
        mat = np.zeros((len(top), len(stems)))
        for j, vd in enumerate(view_data):
            total = vd["total"] or 1
            for i, t in enumerate(top):
                mat[i, j] = 100 * vd["ctr"].get(t, 0) / total
        out = args.output or os.path.join(os.getcwd(), f"cima_view_landscape_{args.level}.png")
        plt = setup_matplotlib()
        fig, ax = plt.subplots(figsize=(10, 6))
        im = ax.imshow(mat, aspect="auto", cmap="Blues")
        ax.set_xticks(range(len(stems)))
        ax.set_xticklabels(stems, rotation=45, ha="right")
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(top, fontsize=8)
        ax.set_title(f"CIMA {args.level} % by view")
        fig.colorbar(im, ax=ax, shrink=0.7)
        import matplotlib.pyplot as mp

        mp.tight_layout()
        fig.savefig(out, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"\nSaved: {out}")


if __name__ == "__main__":
    main()
