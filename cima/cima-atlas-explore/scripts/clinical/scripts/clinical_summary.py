#!/usr/bin/env python3
"""CIMA cohort clinical metadata summary (donor or cell level)."""

from __future__ import annotations

import argparse
import collections
import json
import os
import sys

from bootstrap import prepare_atlas_paths

prepare_atlas_paths()

from cima_constants import AGE_BINS, CLINICAL_COLS, DEFAULT_VIEW
from cima_donors import age_bin, load_donor_table
from io_core import setup_matplotlib


def _summarize_numeric(values: list[float]) -> dict:
    vals = sorted(float(v) for v in values)
    n = len(vals)
    mid = vals[n // 2]
    return {
        "n": n,
        "min": vals[0],
        "max": vals[-1],
        "mean": round(sum(vals) / n, 2),
        "median": mid,
    }


def _bin_counts(values: list[float], bins: list[tuple[int, int]]) -> list[dict]:
    out = []
    n = len(values)
    for lo, hi in bins:
        c = sum(1 for v in values if lo <= float(v) <= hi)
        out.append({"bin": f"{lo}-{hi}", "n": c, "pct": round(100 * c / n, 1) if n else 0})
    return out


def main():
    p = argparse.ArgumentParser(description="CIMA clinical metadata summary.")
    p.add_argument("view", nargs="?", default=DEFAULT_VIEW, help="Catalog stem: PBMCs, B, …")
    p.add_argument("--level", choices=["donor", "cell"], default="donor")
    p.add_argument("--column", "-c", help="Single column (age, sex, BMI, …)")
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument(
        "--fast",
        action="store_true",
        help="Donor level via FTP metadata (428 donors, no h5ad scan)",
    )
    p.add_argument("--plot", action="store_true", help="Age histogram (donor level)")
    p.add_argument("-o", "--output", default=None)
    args = p.parse_args()
    donors: list[dict] | None = None

    if args.level == "donor":
        donors = load_donor_table(args.view, fast=args.fast)
        n_cells = sum(d["n_cells"] for d in donors) if not args.fast else None
        payload = {
            "view": args.view,
            "n_donors": len(donors),
            "columns": {},
        }
        if n_cells is not None:
            payload["n_cells"] = n_cells
        elif args.fast:
            payload["source"] = "ftp_metadata"
        cols = [args.column] if args.column else CLINICAL_COLS
        for col in cols:
            present = [d[col] for d in donors if col in d]
            if not present:
                continue
            if col == "age":
                ages = [float(x) for x in present]
                payload["columns"]["age"] = {
                    **_summarize_numeric(ages),
                    "bins": _bin_counts(ages, AGE_BINS),
                }
            else:
                ctr = collections.Counter(str(x) for x in present)
                payload["columns"][col] = {
                    "n": len(present),
                    "categories": [
                        {"value": k, "n": v, "pct": round(100 * v / len(present), 1)}
                        for k, v in ctr.most_common()
                    ],
                }
    else:
        from io_core import load_obs_column, validate_dataset_dir

        ds = validate_dataset_dir(args.view)
        payload = {"view": args.view, "level": "cell", "columns": {}}
        cols = [args.column] if args.column else CLINICAL_COLS
        for col in cols:
            try:
                arr = load_obs_column(ds, col)
            except FileNotFoundError:
                continue
            n = len(arr)
            if col == "age":
                ages = [float(x) for x in arr]
                payload["columns"]["age"] = {
                    **_summarize_numeric(ages),
                    "bins": _bin_counts(ages, AGE_BINS),
                }
            else:
                ctr = collections.Counter(str(x) for x in arr)
                payload["columns"][col] = {
                    "n": n,
                    "categories": [
                        {"value": k, "n": v, "pct": round(100 * v / n, 1)}
                        for k, v in ctr.most_common(20)
                    ],
                }

    if args.format == "json":
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"View: {args.view}  |  level: {args.level}")
        if args.level == "donor":
            n_cells = payload.get("n_cells")
            if n_cells is not None:
                print(f"Donors: {payload['n_donors']:,}  |  cells: {int(n_cells):,}\n")
            else:
                print(f"Donors: {payload['n_donors']:,}  (FTP metadata)\n")
        for col, info in payload.get("columns", {}).items():
            print(f"=== {col} ===")
            if col == "age":
                print(f"  range {info['min']:.0f}–{info['max']:.0f}  mean {info['mean']}  median {info['median']}")
                for row in info["bins"]:
                    print(f"  {row['bin']:>6}: {row['n']:>4} ({row['pct']:5.1f}%)")
            else:
                for row in info["categories"][:15]:
                    print(f"  {row['value']:<20} {row['n']:>8,} ({row['pct']:5.1f}%)")
                if len(info["categories"]) > 15:
                    print(f"  … +{len(info['categories']) - 15} more")
            print()

    if args.plot and "age" in payload.get("columns", {}) and donors is not None:
        from collections import Counter

        ctr = Counter(int(float(d["age"])) for d in donors)
        ages = sorted(ctr.keys())
        counts = [ctr[a] for a in ages]
        out = args.output or os.path.join(os.getcwd(), args.view, "clinical_age_donors.png")
        os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
        plt = setup_matplotlib()
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.bar(ages, counts, color="#4DBBD5", width=0.8)
        ax.set_xlabel("Age (years)")
        ax.set_ylabel("Donors")
        ax.set_title(f"CIMA {args.view} donor age distribution (n={len(donors)})")
        import matplotlib.pyplot as mp

        mp.tight_layout()
        fig.savefig(out, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"Saved: {out}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
