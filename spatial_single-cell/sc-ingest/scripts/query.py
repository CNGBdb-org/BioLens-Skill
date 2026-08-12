#!/usr/bin/env python3
"""sc-ingest: read matrices -> h5ad."""
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

from scverse_common.io import load_adata, save_adata, make_demo_scrna
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser(description="Ingest scRNA into h5ad")
    sub = ap.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("run"); p.add_argument("input"); p.add_argument("-o", "--outdir", default=None); p.add_argument("--out-h5ad", default=None)
    d = sub.add_parser("demo"); d.add_argument("-o", "--outdir", default=None)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "sc_ingest")
    if args.mode == "demo":
        print_header("sc-ingest", "生成演示数据")
        adata = make_demo_scrna()
        path = save_adata(adata, out / "demo_scrna.h5ad")
    else:
        print_header("sc-ingest", f"读取 {args.input}")
        adata = load_adata(args.input)
        path = save_adata(adata, Path(args.out_h5ad) if args.out_h5ad else out / "ingested.h5ad")
    write_report(out, "sc-ingest", [f"- cells: {adata.n_obs}", f"- genes: {adata.n_vars}", f"- output: `{path}`", f"- obs columns: {list(adata.obs.columns)}"])
    print(f"  cells={adata.n_obs} genes={adata.n_vars}")
    print(f"  h5ad: {path}")
    print(f"  report: {out/'report.md'}")

if __name__ == "__main__":
    main()
