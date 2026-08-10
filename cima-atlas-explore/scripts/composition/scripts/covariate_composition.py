#!/usr/bin/env python3
"""Cell-type proportions by age or sex covariate."""

from __future__ import annotations

import argparse
import collections
import json
import os
import sys

import numpy as np

from bootstrap import prepare_atlas_paths

prepare_atlas_paths()

from cima_constants import AGE_BINS, DEFAULT_VIEW
from cima_donors import age_bin
from io_core import load_obs_column, setup_matplotlib, validate_dataset_dir


def _covariate_bins(covariate: str, values) -> list[str]:
    if covariate == "age":
        return [f"{lo}-{hi}" for lo, hi in AGE_BINS] + ["other"]
    return sorted(set(str(x) for x in values), key=str)


def aggregate(view: str, *, covariate: str, level: str, top_n: int) -> dict:
    ds = validate_dataset_dir(view)
    cov = load_obs_column(ds, covariate)
    labels = load_obs_column(ds, level)
    if covariate == "age":
        groups = np.array([age_bin(float(x)) for x in cov], dtype=object)
    else:
        groups = np.array([str(x) for x in cov], dtype=object)
    labels = np.array([str(x) for x in labels], dtype=object)

    bin_order = _covariate_bins(covariate, cov)
    type_totals = collections.Counter(labels)
    top_types = [t for t, _ in type_totals.most_common(top_n)] if top_n else sorted(type_totals.keys(), key=str)

    by_bin: dict[str, collections.Counter] = {b: collections.Counter() for b in bin_order}
    for g, ct in zip(groups, labels):
        if g not in by_bin:
            by_bin[g] = collections.Counter()
        by_bin[g][ct] += 1

    result_bins = []
    for b in bin_order:
        if b not in by_bin or not by_bin[b]:
            continue
        total = sum(by_bin[b].values())
        result_bins.append({
            "bin": b,
            "n_cells": total,
            "types": {
                t: round(100 * by_bin[b].get(t, 0) / total, 2)
                for t in top_types
            },
        })
    return {"view": view, "covariate": covariate, "level": level, "bins": result_bins, "types": top_types}


def main():
    p = argparse.ArgumentParser(description="Cell-type proportion by age/sex.")
    p.add_argument("view", nargs="?", default=DEFAULT_VIEW)
    p.add_argument("--covariate", default="age", help="age or sex")
    p.add_argument("--level", "-l", default="cell_type_l4")
    p.add_argument("--top", type=int, default=12, help="Top cell types to show")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--plot", action="store_true")
    p.add_argument("-o", "--output", default=None)
    args = p.parse_args()

    data = aggregate(args.view, covariate=args.covariate, level=args.level, top_n=args.top)

    if args.format == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    print(f"View: {args.view}  |  by {args.covariate}  |  {args.level}\n")
    header = f"{'bin':<10}" + "".join(f"{t[:12]:>13}" for t in data["types"])
    print(header)
    for row in data["bins"]:
        line = f"{row['bin']:<10}"
        for t in data["types"]:
            line += f"{row['types'].get(t, 0):>13.1f}"
        print(line)

    if args.plot:
        import matplotlib.pyplot as mp

        types = data["types"]
        bins = [r["bin"] for r in data["bins"]]
        mat = np.array([[r["types"].get(t, 0) for t in types] for r in data["bins"]])
        out = args.output or os.path.join(os.getcwd(), args.view, f"composition_by_{args.covariate}.png")
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        plt = setup_matplotlib()
        fig, ax = plt.subplots(figsize=(10, 5))
        bottom = np.zeros(len(bins))
        colors = plt.cm.tab20(np.linspace(0, 1, len(types)))
        for i, t in enumerate(types):
            ax.bar(bins, mat[:, i], bottom=bottom, label=t, color=colors[i], width=0.7)
            bottom += mat[:, i]
        ax.set_ylabel("Cell fraction (%)")
        ax.set_xlabel(args.covariate)
        ax.set_title(f"CIMA {args.view} composition by {args.covariate}")
        ax.legend(fontsize=6, bbox_to_anchor=(1.02, 1), loc="upper left")
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
