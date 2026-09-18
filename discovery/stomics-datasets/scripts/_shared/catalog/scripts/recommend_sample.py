#!/usr/bin/env python3
"""Recommend catalog samples for tissue / stage queries."""

from __future__ import annotations

import argparse
import json
import sys

from bootstrap import prepare_atlas_paths
from atlas_registry import DEFAULT_OBS_LABEL, get_atlas
import catalog_bridge as cat
from io_core import load_n_obs, load_obs_column, validate_dataset_dir

prepare_atlas_paths()


def _entry_explore_id(e) -> str:
    return (getattr(e, "explore_id", None) or "").strip()


def _has_group(ds, tissue):
    labels = load_obs_column(ds, DEFAULT_OBS_LABEL)
    t = tissue.lower()
    return any(t in str(x).lower() for x in set(labels))


def _structured_reasons(
    item: dict,
    meta: dict,
    *,
    tissue: str | None,
    prefer_demo: bool,
    for_de: bool,
) -> list[dict]:
    reasons: list[dict] = []
    if tissue:
        tissues = item.get("tissues") or []
        if tissues and any(tissue.lower() in str(t).lower() for t in tissues):
            reasons.append({
                "code": "tissue_match",
                "label": f"含 {tissue} 组织",
                "detail": "catalog 标注匹配",
            })
        elif item.get("score", 0) >= 25:
            reasons.append({
                "code": "annotation_match",
                "label": "obs 注释含目标组织",
                "detail": "check-annotation 验证",
            })
    if meta.get("demo_safe") == "1" or item.get("demo_safe"):
        reasons.append({
            "code": "demo_safe",
            "label": "演示推荐",
            "detail": "catalog demo_safe",
        })
    elif prefer_demo:
        pass
    if meta.get("de_ready") == "1" or item.get("de_ready"):
        reasons.append({
            "code": "de_ready",
            "label": "DE-ready",
            "detail": "适合 pseudobulk/差异分析",
        })
    tier = item.get("size_tier") or meta.get("size_tier", "")
    if tier == "small":
        reasons.append({"code": "size", "label": "规模适中", "detail": "small tier"})
    elif tier == "medium":
        reasons.append({"code": "size", "label": "中等规模", "detail": "medium tier"})
    n_spots = item.get("n_spots")
    if n_spots:
        reasons.append({
            "code": "coverage",
            "label": f"{int(n_spots):,} spots",
            "detail": "spot 覆盖高",
        })
    if meta.get("api_mode") == "parquet":
        reasons.append({
            "code": "api",
            "label": "在线 parquet API",
            "detail": "无需下载 h5ad",
        })
    if for_de and not any(r["code"] == "de_ready" for r in reasons):
        reasons.append({
            "code": "fallback",
            "label": "综合评分",
            "detail": f"score={item.get('score', 0):.0f}",
        })
    if not reasons:
        reasons.append({
            "code": "score",
            "label": "综合评分最高",
            "detail": f"score={item.get('score', 0):.0f}",
        })
    return reasons[:4]


def recommend(*, stage=None, tissue=None, technology=None, sex=None, top=5, with_spots=False, check_group=False, prefer_demo=False, for_de=False, slices_only=False):
    spec = get_atlas()
    if spec.name == "hesta":
        rows = cat.search_catalog(stage=stage, tissue=tissue, technology=technology, sex=sex)
        if slices_only:
            from hesta_catalog import is_sagittal_section

            rows = [e for e in rows if is_sagittal_section(e)]
    elif spec.name == "mosta":
        rows = cat.search_catalog(stage=stage, tissue=tissue, kind="sagittal")
        if slices_only:
            rows = [e for e in rows if e.kind == "sagittal" and e.section.lower().endswith(".mosta.h5ad")]
        if not rows:
            rows = cat.search_catalog(stage=stage, kind="sagittal")
        if not rows:
            rows = [e for e in cat.load_catalog() if e.kind == "sagittal"]
    else:
        rows = cat.load_catalog()
        rows = [e for e in rows if cat.is_parquet_section(e)]
        if stage or tissue:
            rows = cat.search_catalog(stage=stage, tissue=tissue) or rows
            rows = [e for e in rows if cat.is_parquet_section(e)]

    try:
        from catalog_enrichment import load_enrichment_index, row_key
        enrich = load_enrichment_index()
    except Exception:
        enrich = {}

    scored = []
    for e in rows:
        s = cat.score_entry(e, tissue=tissue)
        if s is None:
            continue
        rk = row_key(spec.catalog_atlas or spec.name, e.section)
        meta = enrich.get(rk, {})
        if prefer_demo and meta.get("demo_safe") != "1":
            s -= 50
        elif meta.get("demo_safe") == "1":
            s += 40
        if for_de and meta.get("de_ready") != "1":
            s -= 30
        elif meta.get("de_ready") == "1":
            s += 15
        if meta.get("api_mode") == "parquet":
            s += 10
        tier = meta.get("size_tier", "")
        if tier == "small":
            s += 8
        elif tier == "medium":
            s += 5
        elif tier == "huge":
            s -= 10
        item = {
            "dataset_id": e.dataset_id,
            "explore_id": _entry_explore_id(e),
            "section": e.section,
            "stage": e.stage,
            "n_tissues": len(e.tissues),
            "tissues": e.tissues,
            "score": s,
            "size_tier": tier,
            "demo_safe": meta.get("demo_safe") == "1",
            "de_ready": meta.get("de_ready") == "1",
        }
        if spec.name == "hesta":
            item["sex"] = e.sex
            item["technology"] = e.technology
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
        item["reasons"] = _structured_reasons(
            item, meta, tissue=tissue, prefer_demo=prefer_demo, for_de=for_de,
        )
        scored.append(item)

    if spec.name == "hesta":
        scored.sort(key=lambda x: (-x["score"], x["section"]))
    else:
        scored.sort(key=lambda x: (-x["score"], cat.stage_sort_key(x["stage"]), x["section"]))
    return scored[:top]


def main():
    spec = get_atlas()
    p = argparse.ArgumentParser(description=f"Recommend {spec.display_name} samples.")
    p.add_argument("--stage")
    p.add_argument("--tissue", "-t")
    p.add_argument("--top", "-n", type=int, default=5)
    p.add_argument("--with-spots", action="store_true")
    p.add_argument("--prefer-demo", action="store_true", help="Boost demo_safe catalog rows")
    p.add_argument("--for-de", action="store_true", help="Prefer de_ready samples")
    p.add_argument(
        "--slices-only",
        action="store_true",
        help="HESTA/MOSTA: only whole-section sagittal slices (exclude regulon/gene/pathway objects)",
    )
    p.add_argument("--format", choices=["text", "json"], default="text")
    if spec.name == "hesta":
        p.add_argument("--technology")
        p.add_argument("--sex")
        p.add_argument("--check-annotation", action="store_true")
    elif spec.name == "mosta":
        p.add_argument("--check-annotation", action="store_true")
    else:
        p.add_argument("--check-annotation", action="store_true")
        p.add_argument("--kind", help="Filter by Kind column")
    args = p.parse_args()

    if spec.name == "hesta":
        if not any([args.stage, args.tissue, args.technology, args.sex]):
            p.error("Specify at least one of --stage, --tissue, --technology, --sex")
    elif spec.name == "mosta":
        if not any([args.stage, args.tissue]):
            p.error("Specify at least one of --stage, --tissue")
    else:
        if not any([args.stage, args.tissue, getattr(args, "kind", None)]):
            p.error("Specify at least one of --stage, --tissue, --kind")

    results = recommend(
        stage=args.stage,
        tissue=args.tissue,
        technology=getattr(args, "technology", None),
        sex=getattr(args, "sex", None),
        top=args.top,
        with_spots=args.with_spots,
        check_group=getattr(args, "check_annotation", False),
        prefer_demo=getattr(args, "prefer_demo", False),
        for_de=getattr(args, "for_de", False),
        slices_only=getattr(args, "slices_only", False),
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
        if spec.name == "hesta":
            print(f"   {r['stage']} | {r['technology']} | {r['sex']} | {r['n_tissues']} tissues{spots}")
        elif spec.name == "mosta":
            print(f"   {r['stage']} | {r['n_tissues']} tissues{spots}")
        else:
            print(f"   {r['stage']} | {r['n_tissues']} annotation groups{spots}")
        print(f"   section: {r['section']}")
        if args.tissue:
            hit = [t for t in r["tissues"] if args.tissue.lower() in t.lower()]
            if hit:
                print(f"   matching tissue: {', '.join(hit)}")
        print()


if __name__ == "__main__":
    main()
