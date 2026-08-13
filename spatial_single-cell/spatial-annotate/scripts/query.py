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
from scverse_common.spatial import run_spatial_annotate
from scverse_common.report import ensure_outdir, write_report, print_header

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", default=None)
    ap.add_argument("-o", "--outdir", default=None)
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--markers", default=None, help="CSV with columns gene,cell_type")
    ap.add_argument("--key", default="cell_type")
    ap.add_argument("--n-clusters", type=int, default=4)
    args = ap.parse_args()
    out = ensure_outdir(args.outdir, "spatial_annotate")
    if args.demo or args.input is None:
        print_header("spatial-annotate", "demo")
        adata = make_demo_spatial()
        # demo markers from first genes of each domain-biased block
        import pandas as pd
        m = pd.DataFrame({
            "gene": ["SGENE0", "SGENE1", "SGENE8", "SGENE9"],
            "cell_type": ["typeA", "typeA", "typeB", "typeB"],
        })
        mpath = out / "tables" / "demo_markers.csv"
        m.to_csv(mpath, index=False)
        args.markers = str(mpath)
    else:
        print_header("spatial-annotate", args.input)
        adata = load_adata(args.input)
    adata = run_spatial_annotate(
        adata, out, marker_csv=args.markers, label_key=args.key, n_clusters=args.n_clusters
    )
    path = save_adata(adata, out / "annotated.h5ad")
    write_report(out, "spatial-annotate", [
        f"- labels: {adata.obs[args.key].nunique()}",
        f"- key: `{args.key}`",
        f"- method: {adata.uns.get('spatial_annotate', {}).get('method')}",
        f"- h5ad: `{path}`",
        "- figure: `figures/spatial_annotate.png`",
    ])
    print(adata.obs[args.key].value_counts().head().to_string())
    print(f"  -> {path}")

if __name__ == "__main__":
    main()
