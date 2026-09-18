#!/usr/bin/env python3
"""Query PharmGKB / ClinPGx REST API."""

from __future__ import annotations

import argparse
import json
import sys

import requests

# ClinPGx hosts the PharmGKB REST API (api.pharmgkb.org may not resolve in some networks).
BASE = "https://api.clinpgx.org/v1/data"
DISPLAY_LIMIT = 5


def api_get(path: str, params: dict | None = None) -> dict | list:
    r = requests.get(f"{BASE}{path}", params=params, headers={"Accept": "application/json"}, timeout=60)
    r.raise_for_status()
    payload = r.json()
    if isinstance(payload, dict) and "data" in payload:
        if payload.get("status") == "fail":
            errors = (payload.get("data") or {}).get("errors") or []
            msg = errors[0].get("message") if errors else "查询失败"
            raise RuntimeError(msg)
        return payload.get("data") or []
    return payload


def query_gene(symbol: str) -> None:
    print(f"【PharmGKB 查询】基因：{symbol}")
    data = api_get("/gene", {"symbol": symbol})
    items = data if isinstance(data, list) else [data]
    if not items:
        print("  未找到基因")
        return
    g = items[0]
    print(f"  PharmGKB ID: {g.get('id')}")
    print(f"  符号: {g.get('symbol')}  名称: {g.get('name')}")
    print(f"  坐标: {g.get('chr', {}).get('name', 'N/A')}:{g.get('chrStartPosB38')}-{g.get('chrStopPosB38')} (GRCh38)")
    print(f"  CPIC 基因: {g.get('cpicGene', False)}  PharmVar: {g.get('pharmVarGene', False)}")


def query_variant(rsid: str) -> None:
    rs = rsid if rsid.startswith("rs") else f"rs{rsid}"
    print(f"【PharmGKB 查询】变异：{rs}")
    data = api_get("/variant", {"symbol": rs, "view": "base"})
    items = data if isinstance(data, list) else [data]
    if not items:
        print("  未找到变异")
        return
    v = items[0]
    print(f"  PharmGKB ID: {v.get('id')}")
    print(f"  rsID: {v.get('symbol')}")
    print(f"  临床意义: {v.get('clinicalSignificance', 'N/A')}")
    print(f"  变异类型: {v.get('changeClassification', 'N/A')}")


def query_guideline(symbol: str) -> None:
    print(f"【PharmGKB 查询】指南：{symbol}")
    data = api_get("/guidelineAnnotation", {"relatedGenes.symbol": symbol, "view": "base"})
    items = data if isinstance(data, list) else []
    if not items:
        print("  未找到指南注释")
        return
    for i, g in enumerate(items[:DISPLAY_LIMIT], 1):
        print(f"\n  [{i}] {g.get('name', 'N/A')}")
        print(f"      用药信息: {g.get('dosingInformation', False)}  检测建议: {g.get('hasTestingInfo', False)}")
    print(f"\n共 {len(items)} 条，展示前 {min(DISPLAY_LIMIT, len(items))} 条")


def query_clinical(symbol: str) -> None:
    print(f"【PharmGKB 查询】临床注释：{symbol}")
    data = api_get("/clinicalAnnotation", {"location.genes.symbol": symbol, "view": "base"})
    items = data if isinstance(data, list) else []
    if not items:
        print("  未找到临床注释")
        return
    for i, c in enumerate(items[:DISPLAY_LIMIT], 1):
        print(f"\n  [{i}] ID: {c.get('accessionId', c.get('id'))}")
        level = (c.get("levelOfEvidence") or {}).get("term") or c.get("levelOfEvidence", "N/A")
        print(f"      证据等级: {level}")
        phenos = c.get("allelePhenotypes") or []
        if phenos:
            print(f"      表型: {phenos[0].get('phenotype', '')[:120]}...")
    print(f"\n共 {len(items)} 条，展示前 {min(DISPLAY_LIMIT, len(items))} 条")


def query_drug(name: str) -> None:
    print(f"【PharmGKB 查询】药物：{name}")
    data = api_get("/chemical", {"name": name, "view": "base"})
    items = data if isinstance(data, list) else [data]
    if not items:
        print("  未找到药物")
        return
    for i, c in enumerate(items[:DISPLAY_LIMIT], 1):
        print(f"  [{i}] {c.get('name', 'N/A')}  ID: {c.get('id')}")


def query_pathway(keyword: str) -> None:
    print(f"【PharmGKB 查询】通路：{keyword}")
    data = api_get("/pathway", {"name": keyword, "view": "base"})
    items = data if isinstance(data, list) else [data]
    if not items or not items[0]:
        print("  未找到通路")
        return
    for i, p in enumerate(items[:DISPLAY_LIMIT], 1):
        print(f"  [{i}] {p.get('name', 'N/A')}  ID: {p.get('id')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query PharmGKB pharmacogenomics")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("gene", help="Gene pharmacogenomics info").add_argument("symbol")
    sub.add_parser("variant", help="Variant by rsID").add_argument("rsid")
    sub.add_parser("guideline", help="Guideline annotations").add_argument("symbol")
    sub.add_parser("clinical", help="Clinical annotations").add_argument("symbol")
    sub.add_parser("drug", help="Drug/chemical search").add_argument("name")
    sub.add_parser("pathway", help="Pharmacokinetic/dynamic pathway").add_argument("keyword")
    args = parser.parse_args()
    handlers = {
        "gene": lambda: query_gene(args.symbol),
        "variant": lambda: query_variant(args.rsid),
        "guideline": lambda: query_guideline(args.symbol),
        "clinical": lambda: query_clinical(args.symbol),
        "drug": lambda: query_drug(args.name),
        "pathway": lambda: query_pathway(args.keyword),
    }
    try:
        handlers[args.mode]()
    except (requests.RequestException, RuntimeError) as exc:
        print(f"查询失败：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
