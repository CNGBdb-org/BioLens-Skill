#!/usr/bin/env python3
"""Filter merged catalog (datasets_list + enrichment sidecars)."""

from __future__ import annotations

import argparse
import json
import re
import sys

from bootstrap import prepare_atlas_paths
from atlas_registry import get_atlas

prepare_atlas_paths()

_SCRIPTS = __import__("os").path.abspath(
    __import__("os").path.join(
        __import__("os").path.dirname(__import__("os").path.realpath(__file__)),
        "..", "..", "lib", "scripts",
    )
)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from catalog_enrichment import CatalogFilter, filter_merged_rows, iter_merged_catalog  # noqa: E402


def _row_summary(row: dict) -> dict:
    return {
        "atlas": row.get("Atlas"),
        "section": row.get("Section"),
        "explore_id": row.get("ExploreId"),
        "dataset_id": row.get("ExploreId") or row.get("Section"),
        "stage_norm": row.get("stage_norm") or row.get("Developmental stage"),
        "organs_norm": row.get("organs_norm"),
        "api_mode": row.get("api_mode"),
        "size_tier": row.get("size_tier"),
        "n_obs": row.get("n_obs"),
        "demo_safe": row.get("demo_safe"),
        "de_ready": row.get("de_ready"),
        "skill_tags": row.get("skill_tags"),
        "doi": row.get("doi"),
        "dataset_title": row.get("dataset_title"),
    }


def main():
    spec = get_atlas()
    p = argparse.ArgumentParser(description="Filter catalog with enrichment metadata.")
    p.add_argument("--stage")
    p.add_argument("--tissue")
    p.add_argument("--organ", help="Alias for tissue filter on organs_norm")
    p.add_argument("--disease")
    p.add_argument("--kind")
    p.add_argument("--species")
    p.add_argument("--search", "-s")
    p.add_argument("--api-mode", choices=["parquet", "h5ad_only", "none"])
    p.add_argument("--has-spatial", action="store_true")
    p.add_argument("--has-umap", action="store_true")
    p.add_argument("--demo-safe", action="store_true")
    p.add_argument("--de-ready", action="store_true")
    p.add_argument("--size-tier", choices=["tiny", "small", "medium", "large", "huge"])
    p.add_argument("--object-type")
    p.add_argument("--section-plane")
    p.add_argument("--skill-tag", help="e.g. gene_expression, plot_spatial_clusters")
    p.add_argument("--use-case", help="e.g. expression, de, disease")
    p.add_argument("--pmid")
    p.add_argument("--doi")
    p.add_argument("--donor-id")
    p.add_argument("--min-obs", type=int)
    p.add_argument("--max-obs", type=int)
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--format", choices=["text", "json"], default="json")
    args = p.parse_args()

    atlas_key = (spec.catalog_atlas or spec.name).lower()
    if re.match(r"^stds\d+$", spec.name, re.I) or re.match(r"^scds\d+$", spec.name, re.I):
        atlas_key = spec.name.upper()
    rows = iter_merged_catalog(atlas=atlas_key)

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
        demo_safe=True if args.demo_safe else None,
        de_ready=True if args.de_ready else None,
        size_tier=args.size_tier,
        object_type=args.object_type,
        section_plane=args.section_plane,
        skill_tag=args.skill_tag,
        use_case=args.use_case,
        pmid=args.pmid,
        doi=args.doi,
        donor_id=args.donor_id,
        min_obs=args.min_obs,
        max_obs=args.max_obs,
        limit=args.limit,
    )
    matched = filter_merged_rows(rows, flt)

    if args.format == "json":
        print(json.dumps({
            "atlas": spec.name,
            "count": len(matched),
            "datasets": [_row_summary(r) for r in matched],
        }, indent=2, ensure_ascii=False))
        return

    print(f"Matches: {len(matched)}")
    for r in matched:
        print(
            f"{r.get('Atlas'):<12} {r.get('stage_norm',''):<10} "
            f"{r.get('api_mode',''):<10} {r.get('Section','')[:50]}"
        )


if __name__ == "__main__":
    main()
