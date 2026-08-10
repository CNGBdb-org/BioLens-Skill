#!/usr/bin/env python3
"""Batch spatial gene plots."""

import argparse
import os
import sys
import time

from bootstrap import prepare_atlas_paths, shared_root

prepare_atlas_paths()
sys.path.insert(0, os.path.join(shared_root(), "spatial", "scripts"))

from io_core import validate_dataset_dir
from plot_spatial_gene import plot_gene


def main():
    p = argparse.ArgumentParser(description="Batch spatial gene plots.")
    p.add_argument("data_dir")
    p.add_argument("genes", nargs="+")
    p.add_argument("--genes-file", help="One gene per line")
    p.add_argument("-o", "--out-dir", default=None)
    p.add_argument("--fast", action="store_true")
    p.add_argument("--dpi", type=int, default=120)
    p.add_argument("--timing", action="store_true")
    args = p.parse_args()

    ds = validate_dataset_dir(args.data_dir)
    out_dir = args.out_dir or ds.output_dir()
    os.makedirs(out_dir, exist_ok=True)

    genes = list(args.genes)
    if args.genes_file:
        with open(args.genes_file) as f:
            genes.extend(line.strip() for line in f if line.strip() and not line.startswith("#"))

    t0 = time.perf_counter()
    for gene in genes:
        out = os.path.join(out_dir, f"spatial_gene_{gene.replace('/', '_')}.png")
        try:
            plot_gene(ds.dataset_id, gene, out, fast=args.fast, dpi=args.dpi, timing=args.timing)
        except FileNotFoundError as e:
            print(f"Skip {gene}: {e}", file=sys.stderr)
    print(f"Batch done: {len(genes)} genes in {time.perf_counter() - t0:.1f}s → {out_dir}")


if __name__ == "__main__":
    main()
