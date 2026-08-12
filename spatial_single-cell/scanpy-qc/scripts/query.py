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

from scverse_common.io import load_adata, save_adata
from scverse_common.analysis import run_qc
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--outdir", default=None)
    ap.add_argument("--min-genes", type=int, default=200)
    ap.add_argument("--max-mito", type=float, default=20.0)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "scanpy_qc")
    print_header("scanpy-qc", args.input)
    adata = load_adata(args.input)
    filtered, stats = run_qc(adata, out, min_genes=args.min_genes, max_mito=args.max_mito)
    path = save_adata(filtered, out / "qc_filtered.h5ad")
    write_report(out, "scanpy-qc", [f"- {k}: {v}" for k,v in stats.items()] + [f"- output: `{path}`", f"- figure: `figures/qc_violin.png`"])
    print(f"  before={stats['n_before']} after={stats['n_after']}")
    print(f"  h5ad: {path}")
    print(f"  report: {out/'report.md'}")

if __name__ == "__main__":
    main()
