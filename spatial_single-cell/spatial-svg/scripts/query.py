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
from scverse_common.spatial import run_spatial_svg
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("-o", "--outdir", default=None); ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "spatial_svg")
    print_header("spatial-svg", args.input)
    table = run_spatial_svg(load_adata(args.input), out, top_n=args.top)
    write_report(out, "spatial-svg", [f"- top genes: {len(table)}", "- table: `tables/spatial_variable_genes.csv`", "- figure: `figures/top_svg.png`"])
    print(table.head(10).to_string(index=False))
    print(f"  table: {out/'tables'/'spatial_variable_genes.csv'}")

if __name__ == "__main__":
    main()
