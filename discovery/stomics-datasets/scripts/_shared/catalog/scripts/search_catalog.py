#!/usr/bin/env python3
"""Cross-atlas catalog search (no --atlas required)."""

from __future__ import annotations

import argparse
import json
import sys

from bootstrap import prepare_atlas_paths

# Use a benign default so prepare_atlas_paths / get_atlas work for path setup.
prepare_atlas_paths("hesta")

import os

_SCRIPTS = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "lib", "scripts"))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from catalog_enrichment import CatalogFilter, filter_merged_rows, iter_merged_catalog  # noqa: E402


def _row_summary(row: dict) -> dict:
    return {
        "atlas": row.get("Atlas"),
        "section": row.get("Section"),
        "explore_id": row.get("ExploreId"),
        "dataset_id": row.get("ExploreId") or row.get("Section"),
        "species": row.get("Species"),
        "stage": row.get("stage_norm") or row.get("Developmental stage"),
        "tissue": row.get("Tissue"),
        "organs_norm": row.get("organs_norm"),
        "kind": row.get("Kind"),
        "api_mode": row.get("api_mode"),
        "n_obs": row.get("n_obs"),
        "doi": row.get("doi"),
        "dataset_title": row.get("dataset_title"),
        "download": row.get("Download"),
    }


def main():
    p = argparse.ArgumentParser(description="Search all CNGB STOmics/CDCP atlases in datasets_list.tsv")
    p.add_argument("--atlas", help="Optional Atlas column filter (e.g. STDS0000001, hesta)")
    p.add_argument("--stage")
    p.add_argument("--tissue")
    p.add_argument("--organ")
    p.add_argument("--disease")
    p.add_argument("--kind")
    p.add_argument("--species")
    p.add_argument("--search", "-s")
    p.add_argument("--api-mode", choices=["parquet", "h5ad_only", "none"])
    p.add_argument("--has-spatial", action="store_true")
    p.add_argument("--has-umap", action="store_true")
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--format", choices=["text", "json"], default="json")
    args = p.parse_args()

    rows = iter_merged_catalog(atlas=args.atlas)
    flt = CatalogFilter(
        species=args.species,
        tissue=args.tissue,
        organ=args.organ,
        stage=args.stage,
        kind=args.kind,
        disease=args.disease,
        text=args.search,
        api_mode=args.api_mode,
        has_spatial=True if args.has_spatial else None,
        has_umap=True if args.has_umap else None,
        limit=args.limit,
    )
    matched = filter_merged_rows(rows, flt)

    if args.format == "json":
        print(json.dumps({"count": len(matched), "datasets": [_row_summary(r) for r in matched]}, indent=2, ensure_ascii=False))
        return

    print(f"Matches: {len(matched)}")
    for r in matched:
        print(
            f"{(r.get('Atlas') or ''):<14} {(r.get('ExploreId') or r.get('Section') or ''):<40} "
            f"{(r.get('Tissue') or '')[:40]}"
        )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e, file=sys.stderr)
        sys.exit(1)
