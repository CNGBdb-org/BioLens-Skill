#!/usr/bin/env python3
"""CIMA paper curated gene panel UMAP plots."""

from __future__ import annotations

import argparse
import os
import sys
import time

from bootstrap import prepare_atlas_paths, shared_root

prepare_atlas_paths()
sys.path.insert(0, os.path.join(shared_root(), "spatial", "scripts"))

from cima_gene_tables import PAPER_PANELS
from io_core import validate_dataset_dir
from plot_spatial_gene import plot_gene


def main():
    p = argparse.ArgumentParser(description="CIMA paper gene panel plots.")
    p.add_argument("--theme", "-t", choices=sorted(PAPER_PANELS.keys()))
    p.add_argument("view", nargs="?", default=None)
    p.add_argument("--fast", action="store_true")
    p.add_argument("--dpi", type=int, default=120)
    p.add_argument("--list-themes", action="store_true")
    args = p.parse_args()

    if args.list_themes:
        for k, v in PAPER_PANELS.items():
            print(f"{k:16} {v['title']}")
            print(f"                 genes: {', '.join(v['genes'])}")
            print(f"                 default: {v.get('default_sample', '—')}")
        return

    if not args.theme:
        p.error("--theme/-t is required unless --list-themes")

    theme = PAPER_PANELS[args.theme]
    data_dir = args.view or theme.get("default_sample")
    if not data_dir:
        print("Provide view stem for this theme.", file=sys.stderr)
        sys.exit(1)

    ds = validate_dataset_dir(data_dir)
    out_dir = os.path.join(ds.output_dir(), f"paper_panel_{args.theme}")
    os.makedirs(out_dir, exist_ok=True)

    print(f"Theme: {theme['title']}")
    print(f"View:  {ds.dataset_id}")
    print(f"Genes: {', '.join(theme['genes'])}\n")

    t0 = time.perf_counter()
    ok, skip = [], []
    for gene in theme["genes"]:
        out = os.path.join(out_dir, f"spatial_gene_{gene.replace('/', '_')}.png")
        try:
            plot_gene(ds.dataset_id, gene, out, fast=args.fast, dpi=args.dpi)
            ok.append(gene)
        except FileNotFoundError as e:
            print(f"Skip {gene}: {e}", file=sys.stderr)
            skip.append(gene)

    print(f"\nDone: {len(ok)}/{len(theme['genes'])} in {time.perf_counter() - t0:.1f}s → {out_dir}")
    if skip:
        print(f"Skipped: {', '.join(skip)}")


if __name__ == "__main__":
    main()
