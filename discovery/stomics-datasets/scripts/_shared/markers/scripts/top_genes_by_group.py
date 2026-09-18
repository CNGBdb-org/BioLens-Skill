#!/usr/bin/env python3
"""Top genes by mean expression within one obs group (slow)."""

import argparse
import heapq
import json
import sys

import numpy as np

from bootstrap import prepare_atlas_paths
from atlas_registry import DEFAULT_OBS_LABEL

prepare_atlas_paths()

from io_core import load_obs_column, resolve_gene_rel, sample_name, validate_dataset_dir


def top_genes_in_group(data_dir, group_col, group_value, top_n=10, min_mean=0):
    ds = validate_dataset_dir(data_dir)
    labels = load_obs_column(ds, group_col)
    mask = labels == group_value
    group_idx = np.flatnonzero(mask)
    n_group = len(group_idx)
    if n_group == 0:
        available = sorted(set(labels), key=str)[:25]
        raise ValueError(
            f"No spots for {group_col}='{group_value}'. Examples: {', '.join(str(a) for a in available)}"
        )

    heap = []
    for gene in ds.list_genes():
        rel = resolve_gene_rel(ds, gene)
        if not rel:
            continue
        schema = ds.read_parquet_schema(rel)
        if "index" in schema.names:
            t = ds.read_parquet(rel, columns=["index", "value"])
            idx = t["index"].to_numpy()
            val = t["value"].to_numpy()
            m = np.isin(idx, group_idx)
            if not m.any():
                continue
            mean = float(val[m].mean())
        else:
            t = ds.read_parquet(rel, columns=["value"])
            val = t["value"].to_numpy()
            if len(val) != n_group:
                continue
            mean = float(val[group_idx].mean())
        if mean < min_mean:
            continue
        if len(heap) < top_n:
            heapq.heappush(heap, (mean, gene))
        elif mean > heap[0][0]:
            heapq.heapreplace(heap, (mean, gene))

    return sorted(heap, reverse=True)


def main():
    p = argparse.ArgumentParser(description="Top expressed genes in one obs group.")
    p.add_argument("data_dir")
    p.add_argument("-c", "--category", required=True, help="Group name, e.g. Liver")
    p.add_argument("--by", default=DEFAULT_OBS_LABEL)
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--min-mean", type=float, default=0)
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    hits = top_genes_in_group(args.data_dir, args.by, args.category, args.top, args.min_mean)
    if args.format == "json":
        print(json.dumps({
            "sample": sample_name(validate_dataset_dir(args.data_dir)),
            "group": args.category,
            "top_genes": [{"gene": g, "mean": m} for m, g in hits],
        }, indent=2))
        return

    print(f"Top {args.top} genes in {args.by}={args.category} ({args.data_dir}):\n")
    for mean, gene in hits:
        print(f"  {gene:<12} mean={mean:.4f}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError) as e:
        print(e, file=sys.stderr)
        sys.exit(1)
