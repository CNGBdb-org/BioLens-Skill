#!/usr/bin/env python3
"""List / search HESTA catalog TSV."""

import argparse
import json
import sys

from bootstrap import prepare_atlas_paths
import catalog_bridge as cat

prepare_atlas_paths()


def entry_dict(e):
    return {
        "section": e.section,
        "dataset_id": e.dataset_id,
        "explore_id": (getattr(e, "explore_id", None) or "").strip(),
        "stage": e.stage,
        "n_tissues": len(e.tissues),
        "sex": e.sex,
        "technology": e.technology,
        "tissue": e.tissue,
    }


def main():
    p = argparse.ArgumentParser(description="Browse HESTA catalog.")
    p.add_argument("--stage")
    p.add_argument("--tissue")
    p.add_argument("--search", "-s")
    p.add_argument("--technology")
    p.add_argument("--sex")
    p.add_argument("--primary-only", action="store_true", help="Exclude substructure/snRNA objects")
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    path = cat.find_catalog_path()
    if not path:
        print("catalog.tsv not found.", file=sys.stderr)
        sys.exit(1)

    rows = cat.search_catalog(
        stage=args.stage,
        tissue=args.tissue,
        technology=args.technology,
        sex=args.sex,
        text=args.search,
    )
    if args.primary_only:
        rows = [e for e in rows if cat.is_primary_section(e)]
    if not rows and not any([args.stage, args.tissue, args.search, args.technology, args.sex]):
        rows = cat.load_catalog(path)

    if args.format == "json":
        print(json.dumps({"catalog": path, "count": len(rows), "datasets": [entry_dict(e) for e in rows]}, indent=2, ensure_ascii=False))
        return

    print(f"Catalog: {path}")
    print(f"Datasets: {len(rows)}\n")
    print(f"{'dataset_id':<42} {'stage':<10} {'tech':<14} section")
    print("-" * 100)
    for e in rows:
        print(f"{e.dataset_id:<42} {e.stage:<10} {e.technology:<14} {e.section}")


if __name__ == "__main__":
    main()
