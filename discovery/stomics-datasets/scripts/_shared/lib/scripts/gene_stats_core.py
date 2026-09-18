"""Gene expression statistics (shared across atlases)."""

import json

import numpy as np

from io_core import (
    gene_in_var,
    load_gene_sparse,
    load_n_obs,
    load_obs_column,
    resolve_gene_name,
    sample_name,
    validate_dataset_dir,
)
from atlas_registry import get_atlas


def summarize_gene(data_dir, gene, group_by=None, top_groups=0, filter_groups=None):
    ds = validate_dataset_dir(data_dir)
    if get_atlas().fuzzy_gene_symbols:
        resolved = resolve_gene_name(ds, gene)
        if not resolved:
            raise FileNotFoundError(f"Gene '{gene}' not in dataset var / X/")
        gene = resolved
    elif not gene_in_var(ds, gene):
        raise FileNotFoundError(f"Gene '{gene}' not in dataset var / X/")

    n_obs = load_n_obs(ds)
    idx, val = load_gene_sparse(ds, gene)
    n_expr = len(idx)
    pct = 100.0 * n_expr / n_obs if n_obs else 0

    result = {
        "sample": sample_name(ds),
        "dataset_id": ds.dataset_id,
        "gene": gene,
        "n_spots": n_obs,
        "n_expressing": int(n_expr),
        "pct_expressing": round(pct, 2),
        "mean_all_spots": round(float(np.sum(val) / n_obs), 4) if n_obs else 0,
        "mean_expressing": round(float(np.mean(val)), 4) if n_expr else 0,
        "max": round(float(np.max(val)), 4) if n_expr else 0,
    }

    if group_by:
        labels = load_obs_column(ds, group_by)
        vec = np.zeros(n_obs, dtype=np.float32)
        vec[idx] = val.astype(np.float32, copy=False)
        groups = []
        for cat in sorted(set(labels), key=str):
            if filter_groups and str(cat) not in filter_groups:
                continue
            mask = labels == cat
            n_g = int(mask.sum())
            if n_g == 0:
                continue
            sub = vec[mask]
            n_pos = int((sub > 0).sum())
            groups.append({
                group_by: str(cat),
                "n_spots": n_g,
                "n_expressing": n_pos,
                "pct_expressing": round(100.0 * n_pos / n_g, 2),
                "mean_expression": round(float(sub.mean()), 4),
            })
        if top_groups > 0:
            groups.sort(key=lambda x: x["mean_expression"], reverse=True)
            groups = groups[:top_groups]
        result["by_" + group_by] = groups

    return result


def print_summary(data, fmt):
    if fmt == "json":
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    print(f"Sample: {data['sample']}")
    print(f"Gene:   {data['gene']}")
    print(f"Spots:  {data['n_spots']:,}  |  expressing: {data['n_expressing']:,} ({data['pct_expressing']}%)")
    print(
        f"Mean (all spots): {data['mean_all_spots']}  |  "
        f"mean (expressing): {data['mean_expressing']}  |  max: {data['max']}"
    )

    key = next((k for k in data if k.startswith("by_")), None)
    if key:
        col = key[3:]
        print(f"\nBy {col}:")
        print(f"{'group':<24} {'n_spots':>10} {'n_expr':>10} {'pct%':>8} {'mean':>10}")
        for row in data[key]:
            print(
                f"{row[col]:<24} {row['n_spots']:>10,} {row['n_expressing']:>10,} "
                f"{row['pct_expressing']:>8.2f} {row['mean_expression']:>10.4f}"
            )
