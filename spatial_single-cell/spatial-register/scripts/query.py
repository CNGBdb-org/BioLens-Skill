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

from scverse_common.io import load_adata, save_adata, make_demo_spatial_slices
from scverse_common.spatial import run_spatial_register
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("run")
    p.add_argument("inputs", nargs="+")
    p.add_argument("-o", "--outdir", default=None)
    d = sub.add_parser("demo")
    d.add_argument("-o", "--outdir", default=None)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "spatial_register")
    if args.mode == "demo":
        print_header("spatial-register", "demo")
        adatas = make_demo_spatial_slices(n_slices=2)
    else:
        if len(args.inputs) < 2:
            raise SystemExit("run 模式至少需要 2 个 h5ad")
        print_header("spatial-register", ",".join(args.inputs))
        adatas = [load_adata(x) for x in args.inputs]
    adata = run_spatial_register(adatas, out)
    path = save_adata(adata, out / "registered.h5ad")
    write_report(out, "spatial-register", [
        f"- slices: {adata.obs['slice'].nunique() if 'slice' in adata.obs else 'n/a'}",
        f"- spots: {adata.n_obs}",
        f"- method: {adata.uns.get('spatial_register', {}).get('method')}",
        f"- h5ad: `{path}`",
        "- figure: `figures/spatial_register.png`",
    ])
    print(f"  spots={adata.n_obs} -> {path}")

if __name__ == "__main__":
    main()
