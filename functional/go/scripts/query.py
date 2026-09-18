#!/usr/bin/env python3
"""Query Gene Ontology via QuickGO REST API."""

from __future__ import annotations

import argparse
import json
import sys

import requests

ONTOLOGY = "https://www.ebi.ac.uk/QuickGO/services/ontology/go"
ANNOTATION = "https://www.ebi.ac.uk/QuickGO/services/annotation"
DISPLAY_LIMIT = 5


def api_get(url: str, params: dict | None = None) -> dict:
    r = requests.get(url, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def query_term(term_id: str) -> None:
    print(f"【GO 查询】Term：{term_id}")
    tid = term_id.upper().replace("GO:", "GO:") if term_id.upper().startswith("GO") else term_id
    if not tid.startswith("GO:"):
        tid = f"GO:{tid.replace('GO', '')}"
    data = api_get(f"{ONTOLOGY}/terms/{tid}")
    results = data.get("results") or []
    if not results:
        print("  未找到该 term")
        return
    t = results[0]
    print(f"  ID: {t.get('id')}")
    print(f"  名称: {t.get('name')}")
    print(f"  命名空间: {t.get('aspect')}")
    defn = t.get("definition") or {}
    print(f"  定义: {defn.get('text', 'N/A')}")
    syns = [s.get("name") for s in t.get("synonyms") or []][:5]
    if syns:
        print(f"  同义词: {', '.join(syns)}")


def query_search(keyword: str) -> None:
    print(f"【GO 查询】搜索：{keyword}")
    data = api_get(f"{ONTOLOGY}/search", {"query": keyword, "limit": DISPLAY_LIMIT})
    results = data.get("results") or []
    total = data.get("numberOfHits", len(results))
    if not results:
        print("  未找到结果")
        return
    for i, t in enumerate(results, 1):
        print(f"\n  [{i}] {t.get('id')}  {t.get('name')}")
        defn = (t.get("definition") or {}).get("text", "")
        if defn:
            print(f"      {defn[:120]}...")
    print(f"\n共 {total} 条，展示前 {len(results)} 条")


def resolve_uniprot(symbol: str) -> str | None:
    r = requests.get(
        "https://rest.uniprot.org/uniprotkb/search",
        params={"query": f"gene:{symbol} AND organism_id:9606 AND reviewed:true", "format": "json", "size": 1},
        timeout=30,
    )
    r.raise_for_status()
    results = r.json().get("results") or []
    if results:
        return results[0].get("primaryAccession")
    return None


def query_gene(symbol: str) -> None:
    print(f"【GO 查询】基因注释：{symbol}")
    acc = resolve_uniprot(symbol)
    params: dict = {"taxonId": 9606, "limit": DISPLAY_LIMIT}
    if acc:
        params["geneProductId"] = acc
    else:
        params["symbol"] = symbol
    data = api_get(f"{ANNOTATION}/search", params)
    results = data.get("results") or []
    if not results:
        print("  未找到 GO 注释")
        return
    for i, a in enumerate(results, 1):
        print(f"\n  [{i}] {a.get('goId')}  {a.get('goName') or a.get('goAspect')}")
        print(f"      证据: {a.get('goEvidence')}  来源: {a.get('assignedBy')}")
        print(f"      参考: {a.get('reference', 'N/A')}")
    print(f"\n展示前 {len(results)} 条")


def query_ancestors(term_id: str) -> None:
    tid = term_id if term_id.startswith("GO:") else f"GO:{term_id.replace('GO', '')}"
    print(f"【GO 查询】祖先 term：{tid}")
    data = api_get(f"{ONTOLOGY}/term/{tid}/ancestors")
    results = data.get("results") or []
    if not results:
        print("  未找到祖先 term")
        return
    for t in results[:DISPLAY_LIMIT]:
        print(f"  {t.get('id')}  {t.get('name')}  ({t.get('aspect')})")
    if len(results) > DISPLAY_LIMIT:
        print(f"  ... 共 {len(results)} 条")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query Gene Ontology via QuickGO")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("term", help="GO term details").add_argument("term_id")
    sub.add_parser("search", help="Search GO terms").add_argument("keyword")
    sub.add_parser("gene", help="GO annotations for gene").add_argument("gene")
    sub.add_parser("ancestors", help="Ancestor terms").add_argument("term_id")
    args = parser.parse_args()
    handlers = {
        "term": lambda: query_term(args.term_id),
        "search": lambda: query_search(args.keyword),
        "gene": lambda: query_gene(args.gene),
        "ancestors": lambda: query_ancestors(args.term_id),
    }
    try:
        handlers[args.mode]()
    except requests.RequestException as exc:
        print(f"API 请求失败：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
