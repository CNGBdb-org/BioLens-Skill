#!/usr/bin/env python3
"""Recommend HESTA samples for tissue / stage queries."""

from __future__ import annotations

import argparse
import json
import sys

from bootstrap import prepare_atlas_paths
from atlas_registry import DEFAULT_OBS_LABEL
import catalog_bridge as cat
from io_core import load_n_obs, load_obs_column, validate_dataset_dir

prepare_atlas_paths()


def _has_group(ds, tissue):
    labels = load_obs_column(ds, DEFAULT_OBS_LABEL)
    t = tissue.lower()
    return any(t in str(x).lower() for x in set(labels))


def recommend(*, stage=None, tissue=None, technology=None, sex=None, top=5, with_spots=False, check_group=False, slices_only=False):
    rows = cat.search_catalog(stage=stage, tissue=tissue, technology=technology, sex=sex)
    if slices_only:
        rows = [e for e in rows if cat.is_sagittal_section(e)]

    scored = []
    for e in rows:
        s = cat.score_entry(e, tissue=tissue)
        if s is None:
            continue
        item = {
            "dataset_id": e.dataset_id,
            "explore_id": (getattr(e, "explore_id", None) or "").strip(),
            "section": e.section,
            "stage": e.stage,
            "n_tissues": len(e.tissues),
            "tissues": e.tissues,
            "score": s,
            "sex": e.sex,
            "technology": e.technology,
        }
        if with_spots or check_group:
            try:
                ds = validate_dataset_dir(e.dataset_id)
                if with_spots:
                    item["n_spots"] = load_n_obs(ds)
                    item["score"] += min(item["n_spots"] / 100_000, 10)
                if check_group and tissue and not e.tissues:
                    if not _has_group(ds, tissue):
                        continue
                    item["score"] += 25
            except FileNotFoundError:
                if check_group and tissue and not e.tissues:
                    continue
                item["n_spots"] = None
        scored.append(item)

    scored.sort(key=lambda x: (-x["score"], x["section"]))
    return scored[:top]


def main():
    p = argparse.ArgumentParser(description="Recommend HESTA samples.")
    p.add_argument("--stage")
    p.add_argument("--tissue", "-t")
    p.add_argument("--technology")
    p.add_argument("--sex")
    p.add_argument("--top", "-n", type=int, default=5)
    p.add_argument("--with-spots", action="store_true")
    p.add_argument("--check-annotation", action="store_true")
    p.add_argument(
        "--slices-only",
        action="store_true",
        help="Only whole-section sagittal slices (exclude regulon/gene/pathway objects)",
    )
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    if not any([args.stage, args.tissue, args.technology, args.sex]):
        p.error("Specify at least one of --stage, --tissue, --technology, --sex")

    results = recommend(
        stage=args.stage,
        tissue=args.tissue,
        technology=args.technology,
        sex=args.sex,
        top=args.top,
        with_spots=args.with_spots,
        check_group=args.check_annotation,
        slices_only=args.slices_only,
    )

    if args.format == "json":
        print(json.dumps({"recommendations": results}, indent=2, ensure_ascii=False))
        return
    if not results:
        print("No matching samples.")
        return

    q = ", ".join(x for x in [
        f"stage={args.stage}" if args.stage else None,
        f"tissue={args.tissue}" if args.tissue else None,
    ] if x)
    print(f"Top {len(results)} recommendations ({q}):\n")
    for i, r in enumerate(results, 1):
        spots = f", {r['n_spots']:,} spots" if r.get("n_spots") else ""
        print(f"{i}. {r['dataset_id']}")
        print(f"   {r['stage']} | {r['technology']} | {r['sex']} | {r['n_tissues']} tissues{spots}")
        print(f"   section: {r['section']}")
        if args.tissue:
            hit = [t for t in r["tissues"] if args.tissue.lower() in t.lower()]
            if hit:
                print(f"   matching tissue: {', '.join(hit)}")
        print()


if __name__ == "__main__":
    main()
