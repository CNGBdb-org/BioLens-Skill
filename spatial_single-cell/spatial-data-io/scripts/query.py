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

from scverse_common.io import read_spatial_io, save_adata, make_demo_spatial
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("run")
    p.add_argument("input")
    p.add_argument("-o", "--outdir", default=None)
    p.add_argument("--platform", default="auto", choices=["auto", "h5ad", "visium", "10x", "10x_mtx", "10x_h5"])
    d = sub.add_parser("demo")
    d.add_argument("-o", "--outdir", default=None)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "spatial_data_io")
    if args.mode == "demo":
        print_header("spatial-data-io", "demo")
        adata = make_demo_spatial()
        platform = "demo"
    else:
        print_header("spatial-data-io", args.input)
        adata, platform = read_spatial_io(args.input, platform=args.platform)
    path = save_adata(adata, out / "spatial.h5ad")
    write_report(out, "spatial-data-io", [
        f"- platform: {platform}",
        f"- spots: {adata.n_obs}",
        f"- genes: {adata.n_vars}",
        f"- spatial dim: {adata.obsm['spatial'].shape}",
        f"- output: `{path}`",
    ])
    print(f"  platform={platform} spots={adata.n_obs} -> {path}")

if __name__ == "__main__":
    main()
