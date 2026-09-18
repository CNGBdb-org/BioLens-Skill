#!/usr/bin/env python3
"""Suggest pseudobulk / DE sample groups from catalog enrichment (donor/replicate)."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict

from bootstrap import prepare_atlas_paths
from atlas_registry import get_atlas, lookup_atlas

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


def _dataset_id(row: dict) -> str:
    spec = lookup_atlas((row.get("Atlas") or "").lower())
    prefix = spec.api_prefix if spec else ""
    stem = row.get("Section", "")
    if stem.endswith(".h5ad"):
        stem = stem[:-5]
    return f"{prefix}{stem}" if prefix else stem


def main():
    spec = get_atlas()
    p = argparse.ArgumentParser(description="Recommend DE/pseudobulk sample groups from catalog metadata.")
    p.add_argument("--atlas", default=None, help="Defaults to current --atlas context")
    p.add_argument("--tissue")
    p.add_argument("--disease")
    p.add_argument("--min-replicates", type=int, default=2)
    p.add_argument("--format", choices=["json", "text"], default="json")
    args = p.parse_args()

    atlas = args.atlas or spec.catalog_atlas or spec.name
    rows = iter_merged_catalog(atlas=atlas)
    flt = CatalogFilter(
        de_ready=True,
        tissue=args.tissue,
        disease=args.disease,
        limit=0,
    )
    candidates = filter_merged_rows(rows, flt)

    by_donor: dict[str, list[dict]] = defaultdict(list)
    by_condition: dict[str, list[dict]] = defaultdict(list)
    for r in candidates:
        donor = (r.get("donor_id") or "").strip() or (r.get("batch_id") or "").strip()
        if donor:
            by_donor[donor].append(r)
        cond = (r.get("condition") or r.get("Disease") or "all").strip()[:80]
        by_condition[cond].append(r)

    replicate_groups = []
    for donor, group in sorted(by_donor.items()):
        if len(group) >= args.min_replicates:
            replicate_groups.append({
                "type": "technical_replicates",
                "donor_id": donor,
                "n_samples": len(group),
                "samples": [_dataset_id(x) for x in group[:12]],
            })

    condition_pairs = []
    cond_keys = [k for k in by_condition if k and k != "all"]
    if len(cond_keys) >= 2:
        for i, a in enumerate(cond_keys[:5]):
            for b in cond_keys[i + 1 : i + 2]:
                condition_pairs.append({
                    "type": "condition_contrast",
                    "group_a": a,
                    "group_b": b,
                    "n_a": len(by_condition[a]),
                    "n_b": len(by_condition[b]),
                    "samples_a": [_dataset_id(x) for x in by_condition[a][:6]],
                    "samples_b": [_dataset_id(x) for x in by_condition[b][:6]],
                })

    solo = [
        {
            "dataset_id": _dataset_id(r),
            "section": r.get("Section"),
            "n_obs": r.get("n_obs"),
            "size_tier": r.get("size_tier"),
            "de_ready": r.get("de_ready") == "1",
        }
        for r in candidates[:20]
    ]

    out = {
        "atlas": atlas,
        "n_candidates": len(candidates),
        "replicate_groups": replicate_groups[:15],
        "condition_contrasts": condition_pairs[:10],
        "solo_de_candidates": solo,
        "hint": "Use de_two_groups for exploratory Wilcoxon; pseudobulk + DESeq2 in Jupyter notebook 02.",
    }

    if args.format == "json":
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    print(json.dumps(out, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
