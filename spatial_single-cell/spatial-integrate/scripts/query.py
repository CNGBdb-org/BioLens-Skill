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

import anndata as ad
from scverse_common.io import load_adata, save_adata, make_demo_spatial_slices
from scverse_common.spatial import run_spatial_integrate
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", default=None)
    ap.add_argument("-o", "--outdir", default=None)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--batch-key", default="batch")
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "spatial_integrate")
    if args.demo or args.input is None:
        print_header("spatial-integrate", "demo")
        slices = make_demo_spatial_slices(n_slices=2)
        adata = ad.concat(slices, join="inner", index_unique="-")
    else:
        print_header("spatial-integrate", args.input)
        adata = load_adata(args.input)
    adata, stats = run_spatial_integrate(adata, out, batch_key=args.batch_key)
    path = save_adata(adata, out / "integrated.h5ad")
    write_report(out, "spatial-integrate", [
        f"- method: {stats['method']}",
        f"- spots: {stats['n_spots']}",
        f"- batches: {stats['batches']}",
        f"- h5ad: `{path}`",
        "- figure: `figures/spatial_integrate.png`",
    ])
    print(f"  method={stats['method']} spots={stats['n_spots']} -> {path}")

if __name__ == "__main__":
    main()
