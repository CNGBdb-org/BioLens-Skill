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
from scverse_common.analysis import run_preprocess
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--outdir", default=None)
    ap.add_argument("--n-top-genes", type=int, default=2000)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "scanpy_preprocess")
    print_header("scanpy-preprocess", args.input)
    adata = run_preprocess(load_adata(args.input), out, n_top_genes=args.n_top_genes)
    path = save_adata(adata, out / "preprocessed.h5ad")
    write_report(out, "scanpy-preprocess", [f"- cells: {adata.n_obs}", f"- HVG genes kept: {adata.n_vars}", f"- PCA: {adata.obsm['X_pca'].shape}", f"- output: `{path}`"])
    print(f"  cells={adata.n_obs} hvg={adata.n_vars} pcs={adata.obsm['X_pca'].shape[1]}")
    print(f"  h5ad: {path}")

if __name__ == "__main__":
    main()
