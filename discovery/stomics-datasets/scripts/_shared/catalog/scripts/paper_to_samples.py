#!/usr/bin/env python3
"""Map DOI/PMID/atlas title → catalog samples (literature sidecar)."""

from __future__ import annotations

import argparse
import json
import re
import sys

from bootstrap import prepare_atlas_paths

prepare_atlas_paths()

_SCRIPTS = __import__("os").path.abspath(
    __import__("os").path.join(
        __import__("os").path.dirname(__import__("os").path.realpath(__file__)),
        "..", "..", "lib", "scripts",
    )
)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from catalog_enrichment import filter_merged_rows, iter_merged_catalog, CatalogFilter  # noqa: E402
from atlas_registry import lookup_atlas  # noqa: E402


def _sample_dict(row: dict) -> dict:
    spec = lookup_atlas((row.get("Atlas") or "").lower())
    prefix = spec.api_prefix if spec else ""
    stem = row.get("Section", "")
    if stem.endswith(".h5ad"):
        stem = stem[:-5]
    dataset_id = f"{prefix}{stem}" if prefix else stem
    return {
        "atlas": row.get("Atlas"),
        "dataset_id": dataset_id,
        "section": row.get("Section"),
        "explore_id": row.get("ExploreId"),
        "stage_norm": row.get("stage_norm"),
        "organs_norm": row.get("organs_norm"),
        "doi": row.get("doi"),
        "dataset_title": row.get("dataset_title"),
        "demo_safe": row.get("demo_safe") == "1",
        "api_mode": row.get("api_mode"),
    }


def main():
    p = argparse.ArgumentParser(description="Find catalog samples for a paper or dataset title.")
    p.add_argument("query", nargs="?", help="DOI, PMID, atlas name, or title keywords")
    p.add_argument("--doi", help="DOI e.g. 10.1038/s41586-026-10545-0")
    p.add_argument("--pmid")
    p.add_argument("--atlas", help="hesta / mosta / STDS0000001")
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--demo-only", action="store_true")
    p.add_argument("--format", choices=["json", "text"], default="json")
    args = p.parse_args()

    q = (args.query or args.doi or args.pmid or args.atlas or "").strip()
    if not q:
        print("Provide query, --doi, --pmid, or --atlas", file=sys.stderr)
        sys.exit(1)

    rows = iter_merged_catalog()
    flt = CatalogFilter(limit=0)
    if args.demo_only:
        flt.demo_safe = True
    if args.doi or re.search(r"10\.\d{4,}/", q):
        flt.doi = args.doi or q
    elif args.pmid or re.search(r"^\d{7,8}$", q):
        flt.pmid = args.pmid or q
    elif args.atlas:
        flt.atlas = args.atlas
    else:
        flt.text = q

    matched = filter_merged_rows(rows, flt)
    if not matched and not (args.doi or args.pmid):
        # atlas name shortcut
        flt2 = CatalogFilter(atlas=q.lower(), limit=0)
        matched = filter_merged_rows(rows, flt2)
    if not matched:
        flt3 = CatalogFilter(text=q, limit=0)
        matched = filter_merged_rows(rows, flt3)

    if args.limit:
        matched = matched[: args.limit]

    samples = [_sample_dict(r) for r in matched]
    if args.format == "json":
        print(json.dumps({"query": q, "count": len(samples), "samples": samples}, indent=2, ensure_ascii=False))
        return

    print(f"Query: {q}  →  {len(samples)} samples")
    for s in samples:
        print(f"  {s['atlas']}\t{s['dataset_id']}\t{s.get('stage_norm','')}")


if __name__ == "__main__":
    main()
