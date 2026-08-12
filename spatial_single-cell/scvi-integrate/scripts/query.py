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
from scverse_common.analysis import run_scvi_or_fallback
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--outdir", default=None)
    ap.add_argument("--batch-key", default="batch")
    ap.add_argument("--max-epochs", type=int, default=50)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "scvi_integrate")
    print_header("scvi-integrate", args.input)
    adata, stats = run_scvi_or_fallback(load_adata(args.input), out, batch_key=args.batch_key, max_epochs=args.max_epochs)
    path = save_adata(adata, out / "scvi_integrated.h5ad")
    write_report(out, "scvi-integrate", [f"- {k}: {v}" for k,v in stats.items()] + [f"- output: `{path}`"])
    print(f"  method={stats.get('method')} mixing={stats.get('batch_mixing_knn', 'NA')}")
    if "note" in stats: print(f"  note: {stats['note']}")
    print(f"  h5ad: {path}")

if __name__ == "__main__":
    main()
