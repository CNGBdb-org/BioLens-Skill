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
from scverse_common.analysis import run_cluster
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--outdir", default=None)
    ap.add_argument("--resolution", type=float, default=0.5)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "scanpy_cluster")
    print_header("scanpy-cluster", args.input)
    adata = run_cluster(load_adata(args.input), out, resolution=args.resolution)
    path = save_adata(adata, out / "clustered.h5ad")
    n = adata.obs['leiden'].nunique()
    write_report(out, "scanpy-cluster", [f"- clusters: {n}", f"- resolution: {args.resolution}", f"- output: `{path}`", "- figure: `figures/umap_leiden.png`"])
    print(f"  clusters={n}")
    print(f"  h5ad: {path}")

if __name__ == "__main__":
    main()
