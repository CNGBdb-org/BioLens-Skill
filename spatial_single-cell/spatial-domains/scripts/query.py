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
from scverse_common.spatial import run_spatial_domains
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", default=None)
    ap.add_argument("-o", "--outdir", default=None)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--n-domains", type=int, default=4)
    ap.add_argument("--key", default="domain")
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "spatial_domains")
    if args.demo or args.input is None:
        print_header("spatial-domains", "demo")
        adata = make_demo_spatial()
    else:
        print_header("spatial-domains", args.input)
        adata = load_adata(args.input)
    adata = run_spatial_domains(adata, out, n_domains=args.n_domains, key=args.key)
    path = save_adata(adata, out / "domains.h5ad")
    write_report(out, "spatial-domains", [
        f"- spots: {adata.n_obs}",
        f"- domains: {adata.obs[args.key].nunique()}",
        f"- key: `{args.key}`",
        f"- method: {adata.uns.get('spatial_domains', {}).get('method')}",
        f"- h5ad: `{path}`",
        "- figure: `figures/spatial_domains.png`",
    ])
    print(f"  domains={adata.obs[args.key].nunique()} -> {path}")

if __name__ == "__main__":
    main()
