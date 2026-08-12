#!/usr/bin/env python3
from __future__ import annotations
import argparse
from pathlib import Path
import sys

def _boot():
    here = Path(__file__).resolve().parent
    for p in here.parents:
        if (p / "scverse_common").is_dir():
            sys.path.insert(0, str(p)); return
_boot()

from scverse_common.io import load_adata
from scverse_common.spatial import run_spatial_deconv
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("-o", "--outdir", default=None); ap.add_argument("--factors", type=int, default=4)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "spatial_deconv")
    print_header("spatial-deconv", args.input)
    prop = run_spatial_deconv(load_adata(args.input), out, n_factors=args.factors)
    write_report(out, "spatial-deconv", [f"- factors: {prop.shape[1]}", f"- spots: {prop.shape[0]}", "- baseline: NMF", "- table: `tables/deconv_proportions.csv`"])
    print(prop.head().to_string())
    print(f"  table: {out/'tables'/'deconv_proportions.csv'}")

if __name__ == "__main__":
    main()
