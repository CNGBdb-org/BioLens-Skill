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

from scverse_common.io import load_adata, save_adata, make_demo_spatial
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("run"); p.add_argument("input"); p.add_argument("-o", "--outdir", default=None)
    d = sub.add_parser("demo"); d.add_argument("-o", "--outdir", default=None)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "spatial_ingest")
    if args.mode == "demo":
        print_header("spatial-ingest", "demo")
        adata = make_demo_spatial()
    else:
        print_header("spatial-ingest", args.input)
        adata = load_adata(args.input)
        if "spatial" not in adata.obsm:
            raise SystemExit("输入缺少 obsm['spatial']。可用 demo 或提供 Visium-like h5ad。")
    path = save_adata(adata, out / "spatial.h5ad")
    write_report(out, "spatial-ingest", [f"- spots: {adata.n_obs}", f"- genes: {adata.n_vars}", f"- spatial dim: {adata.obsm['spatial'].shape}", f"- output: `{path}`"])
    print(f"  spots={adata.n_obs} genes={adata.n_vars}")
    print(f"  h5ad: {path}")

if __name__ == "__main__":
    main()
