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
from scverse_common.spatial import run_spatial_trajectory
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", default=None)
    ap.add_argument("-o", "--outdir", default=None)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--root", default=None)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "spatial_trajectory")
    if args.demo or args.input is None:
        print_header("spatial-trajectory", "demo")
        adata = make_demo_spatial()
    else:
        print_header("spatial-trajectory", args.input)
        adata = load_adata(args.input)
    adata = run_spatial_trajectory(adata, out, root=args.root)
    path = save_adata(adata, out / "trajectory.h5ad")
    meta = adata.uns.get("spatial_trajectory", {})
    write_report(out, "spatial-trajectory", [
        f"- root: {meta.get('root')}",
        f"- method: {meta.get('method')}",
        f"- spots: {adata.n_obs}",
        f"- h5ad: `{path}`",
        "- figure: `figures/spatial_trajectory.png`",
        "- table: `tables/pseudotime.csv`",
    ])
    print(f"  root={meta.get('root')} method={meta.get('method')} -> {path}")

if __name__ == "__main__":
    main()
