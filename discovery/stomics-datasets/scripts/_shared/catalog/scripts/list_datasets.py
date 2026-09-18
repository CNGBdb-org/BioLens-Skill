#!/usr/bin/env python3
"""List / search catalog TSV."""

import argparse
import json
import sys

from bootstrap import prepare_atlas_paths
from atlas_registry import get_atlas
import catalog_bridge as cat

prepare_atlas_paths()


def _entry_explore_id(e) -> str:
    return (getattr(e, "explore_id", None) or "").strip()


def entry_dict(e):
    spec = get_atlas()
    explore_id = _entry_explore_id(e)
    d = {
        "section": e.section,
        "dataset_id": e.dataset_id,
        "explore_id": explore_id,
        "stage": e.stage,
        "n_tissues": len(e.tissues),
    }
    if spec.name == "hesta":
        d.update(sex=e.sex, technology=e.technology, tissue=e.tissue)
    else:
        d.update(kind=e.kind, technology=getattr(e, "technology", "") or "")
        if e.tissues:
            d["tissues"] = e.tissues
        if e.download:
            d["download"] = e.download
    return d


def main():
    spec = get_atlas()
    p = argparse.ArgumentParser(description=f"Browse {spec.display_name} catalog.")
    p.add_argument("--stage")
    p.add_argument("--tissue")
    p.add_argument("--search", "-s")
    p.add_argument("--format", choices=["text", "json"], default="text")
    if spec.name == "hesta":
        p.add_argument("--technology")
        p.add_argument("--sex")
    elif spec.name == "mosta":
        p.add_argument("--kind", choices=["sagittal", "cell_bin", "aggregate", "other"])
        p.add_argument("--sagittal-only", action="store_true")
    else:
        p.add_argument("--kind", help="Filter by Kind column in datasets_list.tsv")
        if spec.name == "mccsta":
            p.add_argument("--sagittal-only", action="store_true", help="Alias for --kind sagittal_bin200")
            p.add_argument("--coronal-only", action="store_true")
    p.add_argument("--demo-safe", action="store_true", help="Only demo-safe samples (enrichment sidecar)")
    p.add_argument("--de-ready", action="store_true", help="Only DE-ready samples")
    p.add_argument("--api-mode", choices=["parquet", "h5ad_only", "none"])
    p.add_argument("--size-tier", choices=["tiny", "small", "medium", "large", "huge"])
    args = p.parse_args()

    path = cat.find_catalog_path()
    if not path:
        print(f"{spec.catalog_list_name} not found.", file=sys.stderr)
        sys.exit(1)

    if spec.name == "hesta":
        rows = cat.search_catalog(
            stage=args.stage, tissue=args.tissue,
            technology=args.technology, sex=args.sex, text=args.search,
        )
    elif spec.name == "mosta":
        kind = "sagittal" if args.sagittal_only else args.kind
        rows = cat.search_catalog(stage=args.stage, kind=kind, tissue=args.tissue, text=args.search)
        rows = sorted(rows, key=lambda e: (cat.stage_sort_key(e.stage), e.section))
    else:
        kind = args.kind
        if spec.name == "mccsta":
            if args.sagittal_only:
                kind = "sagittal_bin200"
            if getattr(args, "coronal_only", False):
                kind = "coronal_bin200"
        rows = cat.search_catalog(stage=args.stage, kind=kind, tissue=args.tissue, text=args.search)
        rows = sorted(rows, key=lambda e: (cat.slice_sort_key(e), e.section))

    if any([
        getattr(args, "demo_safe", False),
        getattr(args, "de_ready", False),
        getattr(args, "api_mode", None),
        getattr(args, "size_tier", None),
    ]):
        from catalog_enrichment import load_enrichment_index, row_key

        enrich = load_enrichment_index()
        atlas_key = (spec.catalog_atlas or spec.name).lower()

        def _passes(e) -> bool:
            meta = enrich.get(row_key(atlas_key, e.section), {})
            if getattr(args, "demo_safe", False) and meta.get("demo_safe") != "1":
                return False
            if getattr(args, "de_ready", False) and meta.get("de_ready") != "1":
                return False
            if getattr(args, "api_mode", None) and meta.get("api_mode") != args.api_mode:
                return False
            if getattr(args, "size_tier", None) and meta.get("size_tier") != args.size_tier:
                return False
            return True

        rows = [e for e in rows if _passes(e)]

    if not rows and not any(v for k, v in vars(args).items() if k not in ("format",) and v):
        rows = cat.load_catalog(path)

    if args.format == "json":
        print(json.dumps({"catalog": path, "count": len(rows), "datasets": [entry_dict(e) for e in rows]}, indent=2, ensure_ascii=False))
        return

    print(f"Catalog: {path}")
    print(f"Datasets: {len(rows)}\n")
    if spec.name == "hesta":
        print(f"{'dataset_id':<42} {'stage':<10} {'tech':<14} section")
        print("-" * 100)
        for e in rows:
            print(f"{e.dataset_id:<42} {e.stage:<10} {e.technology:<14} {e.section}")
    elif spec.name == "mosta":
        print(f"{'dataset_id':<48} {'stage':<8} {'kind':<10} section")
        print("-" * 100)
        for e in rows:
            print(f"{e.dataset_id:<48} {e.stage:<8} {e.kind:<10} {e.section}")
    else:
        print(f"{'dataset_id':<22} {'kind':<16} {'tech':<18} section")
        print("-" * 90)
        for e in rows:
            tech = getattr(e, "technology", "") or ""
            print(f"{e.dataset_id:<22} {e.kind:<16} {tech:<18} {e.section}")


if __name__ == "__main__":
    main()
