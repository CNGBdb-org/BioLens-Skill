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
from scverse_common.spatial import run_spatial_qc
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("input"); ap.add_argument("-o", "--outdir", default=None)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "spatial_qc")
    print_header("spatial-qc", args.input)
    stats = run_spatial_qc(load_adata(args.input), out)
    write_report(out, "spatial-qc", [f"- {k}: {v}" for k,v in stats.items()] + ["- figure: `figures/spatial_qc.png`"])
    print(f"  spots={stats['n_spots']} median_counts={stats['median_counts']:.1f}")
    print(f"  report: {out/'report.md'}")

if __name__ == "__main__":
    main()
