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
from scverse_common.spatial import run_spatial_interaction
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("-o", "--outdir", default=None); ap.add_argument("--label-key", default="domain")
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "spatial_interaction")
    print_header("spatial-interaction", args.input)
    mat = run_spatial_interaction(load_adata(args.input), out, label_key=args.label_key)
    write_report(out, "spatial-interaction", [f"- labels: {list(mat.index)}", "- table: `tables/spatial_interaction.csv`", "- figure: `figures/spatial_interaction.png`"])
    print(mat.round(3).to_string())
    print(f"  table: {out/'tables'/'spatial_interaction.csv'}")

if __name__ == "__main__":
    main()
