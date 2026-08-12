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

from scverse_common.io import make_demo_scrna, save_adata, split_demo_batches
from scverse_common.analysis import run_multi_integrate
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("run"); p.add_argument("inputs", nargs="+"); p.add_argument("-o", "--outdir", default=None); p.add_argument("--batch-key", default="batch")
    d = sub.add_parser("demo"); d.add_argument("-o", "--outdir", default=None)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "sc_multi_integrate")
    if args.mode == "demo":
        print_header("sc-multi-integrate", "demo")
        demo = make_demo_scrna()
        batches = split_demo_batches(demo)
        paths = []
        for i, b in enumerate(batches):
            path = save_adata(b, out / f"demo_batch{i}.h5ad")
            paths.append(str(path))
    else:
        print_header("sc-multi-integrate", f"{len(args.inputs)} datasets")
        paths = args.inputs
    adata, stats = run_multi_integrate(paths, out, batch_key=getattr(args, "batch_key", "batch"))
    path = save_adata(adata, out / "integrated.h5ad")
    write_report(out, "sc-multi-integrate", [f"- {k}: {v}" for k,v in stats.items()] + ["- figures: before/after batch UMAP", f"- output: `{path}`"])
    print(f"  method={stats['method']} mixing={stats['batch_mixing_knn']:.3f} cells={stats['n_cells']}")
    print(f"  h5ad: {path}")

if __name__ == "__main__":
    main()
