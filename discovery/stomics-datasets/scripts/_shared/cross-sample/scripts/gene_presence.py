#!/usr/bin/env python3
"""Find which catalog samples contain a gene."""

import argparse
import json
import sys

from bootstrap import prepare_atlas_paths
from atlas_registry import get_atlas
import catalog_bridge as cat
from gene_map_core import filter_catalog_entries
from gene_stats_core import summarize_gene
from io_core import gene_in_var, validate_dataset_dir

prepare_atlas_paths()


def main():
    spec = get_atlas()
    p = argparse.ArgumentParser(description=f"Gene presence across {spec.display_name} catalog.")
    p.add_argument("-g", "--gene", required=True)
    p.add_argument("--stage", help="Filter by stage")
    p.add_argument("--tissue", help="Filter by tissue in catalog")
    p.add_argument("--all-sections", action="store_true")
    if spec.name == "mosta":
        p.add_argument("--sagittal-only", action="store_true", default=True)
        p.add_argument("--no-sagittal-only", action="store_true", dest="no_sagittal", help="Include all kinds")
    elif spec.name == "mccsta":
        p.add_argument("--parquet-only", action="store_true", default=True, help="Only Bin200 spatial (default)")
        p.add_argument("--all-kinds", action="store_true", help="Include snRNA and other kinds")
    p.add_argument("--detection", action="store_true")
    p.add_argument("--min-pct", type=float, default=0)
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    entries = cat.search_catalog(stage=args.stage, tissue=args.tissue) if (args.stage or args.tissue) else cat.load_catalog()
    sagittal_only = True
    if spec.name == "mosta" and args.no_sagittal:
        sagittal_only = False
    all_sections = args.all_sections
    if spec.name == "mccsta" and args.all_kinds:
        all_sections = True
    entries = filter_catalog_entries(entries, all_sections=all_sections, sagittal_only=sagittal_only)

    present = []
    for e in entries:
        try:
            ds = validate_dataset_dir(e.dataset_id)
            if not gene_in_var(ds, args.gene):
                continue
            item = {"dataset_id": e.dataset_id, "section": e.section, "stage": e.stage}
            if args.detection:
                stats = summarize_gene(e.dataset_id, args.gene)
                item["pct_expressing"] = stats["pct_expressing"]
                item["mean_all_spots"] = stats["mean_all_spots"]
                item["gene"] = stats["gene"]
                if stats["pct_expressing"] < args.min_pct:
                    continue
            present.append(item)
        except (FileNotFoundError, OSError):
            continue

    if args.format == "json":
        print(json.dumps({
            "gene": args.gene,
            "n_checked": len(entries),
            "n_present": len(present),
            "present": present,
        }, indent=2, ensure_ascii=False))
        return

    gene_label = present[0].get("gene", args.gene) if present else args.gene
    print(f"Gene: {gene_label}")
    print(f"In var: {len(present)} / {len(entries)} samples\n")
    if args.detection:
        w = 10 if spec.name == "hesta" else 8
        print(f"{'stage':<{w}} {'pct%':>8} {'mean':>10}  dataset")
        for r in present:
            print(f"{r['stage']:<{w}} {r['pct_expressing']:>8.1f} {r['mean_all_spots']:>10.4f}  {r['dataset_id']}")
    else:
        for r in present:
            print(f"{r['stage']:<10}  {r['section']}  →  {r['dataset_id']}")


if __name__ == "__main__":
    main()
