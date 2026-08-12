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
from scverse_common.analysis import run_markers
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--outdir", default=None)
    ap.add_argument("--groupby", default="leiden")
    ap.add_argument("--n-genes", type=int, default=10)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "scanpy_markers")
    print_header("scanpy-markers", args.input)
    table = run_markers(load_adata(args.input), out, groupby=args.groupby, n_genes=args.n_genes)
    write_report(out, "scanpy-markers", [f"- groupby: {args.groupby}", f"- rows: {len(table)}", "- table: `tables/markers.csv`"])
    print(table.head(12).to_string(index=False))
    print(f"  table: {out/'tables'/'markers.csv'}")

if __name__ == "__main__":
    main()
