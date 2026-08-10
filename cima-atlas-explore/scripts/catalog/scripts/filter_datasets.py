#!/usr/bin/env python3
"""Filter HESTA catalog by stage / tissue / text."""

from __future__ import annotations

import argparse
import json
import sys

from bootstrap import prepare_atlas_paths
import catalog_bridge as cat

prepare_atlas_paths()


def _row_summary(e) -> dict:
    return {
        "section": e.section,
        "dataset_id": e.dataset_id,
        "explore_id": (getattr(e, "explore_id", None) or "").strip(),
        "stage": e.stage,
        "technology": e.technology,
        "sex": e.sex,
        "tissues": e.tissues,
        "n_tissues": len(e.tissues),
        "primary": cat.is_primary_section(e),
    }


def main():
    p = argparse.ArgumentParser(description="Filter HESTA catalog.")
    p.add_argument("--stage")
    p.add_argument("--tissue")
    p.add_argument("--organ", help="Alias for --tissue")
    p.add_argument("--technology")
    p.add_argument("--sex")
    p.add_argument("--search", "-s")
    p.add_argument("--primary-only", action="store_true")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--format", choices=["text", "json"], default="json")
    args = p.parse_args()

    rows = cat.search_catalog(
        stage=args.stage,
        tissue=args.tissue or args.organ,
        technology=args.technology,
        sex=args.sex,
        text=args.search,
    )
    if args.primary_only:
        rows = [e for e in rows if cat.is_primary_section(e)]
    if args.limit and args.limit > 0:
        rows = rows[: args.limit]

    if args.format == "json":
        print(json.dumps({
            "atlas": "hesta",
            "count": len(rows),
            "datasets": [_row_summary(e) for e in rows],
        }, indent=2, ensure_ascii=False))
        return

    print(f"Matches: {len(rows)}")
    for e in rows:
        print(f"{e.stage:<10} {e.technology:<14} {e.section}")


if __name__ == "__main__":
    main()
