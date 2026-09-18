#!/usr/bin/env python3
"""Query KEGG REST API — pathway, gene, disease, compound."""

from __future__ import annotations

import argparse
import sys
import urllib.parse

import requests

BASE = "https://rest.kegg.jp"
DISPLAY_LIMIT = 5


def kegg_get(path: str) -> str:
    r = requests.get(f"{BASE}/{path}", timeout=30)
    r.raise_for_status()
    return r.text


def find_gene_id(symbol: str) -> str | None:
    text = kegg_get(f"find/genes/{urllib.parse.quote(symbol)}")
    for line in text.strip().splitlines():
        if line.startswith("hsa:"):
            parts = line.split("\t")
            name_field = parts[1] if len(parts) > 1 else ""
            if symbol.upper() in name_field.upper().split(",")[0].split(";")[0]:
                return parts[0].strip()
    for line in text.strip().splitlines():
        if line.startswith("hsa:"):
            return line.split("\t")[0].strip()
    return None


def query_gene(symbol: str) -> None:
    print(f"【KEGG 查询】基因：{symbol}")
    kid = find_gene_id(symbol)
    if not kid:
        print("  未找到 KEGG 基因 ID")
        return
    print(f"  KEGG ID: {kid}")
    entry = kegg_get(f"get/{kid}")
    for line in entry.splitlines()[:20]:
        print(f"  {line}")
    links = kegg_get(f"link/pathway/{kid}").strip().splitlines()
    if links:
        print(f"\n  关联通路（前 {DISPLAY_LIMIT} 个）:")
        for line in links[:DISPLAY_LIMIT]:
            parts = line.split("\t")
            if len(parts) >= 2:
                print(f"    {parts[1]}")


def query_pathway(pathway_id: str) -> None:
    pid = pathway_id if pathway_id.startswith("hsa") else f"hsa{pathway_id.replace('path:', '')}"
    if not pid.startswith("hsa"):
        pid = f"hsa{pid}"
    print(f"【KEGG 查询】通路：{pid}")
    entry = kegg_get(f"get/{pid}")
    for line in entry.splitlines()[:25]:
        print(f"  {line}")


def query_disease(keyword: str) -> None:
    print(f"【KEGG 查询】疾病：{keyword}")
    text = kegg_get(f"find/disease/{urllib.parse.quote(keyword)}")
    lines = [l for l in text.strip().splitlines() if l]
    if not lines:
        print("  未找到疾病")
        return
    for line in lines[:DISPLAY_LIMIT]:
        parts = line.split("\t")
        print(f"  {parts[0]}  {parts[1] if len(parts) > 1 else ''}")
    print(f"\n共 {len(lines)} 条，展示前 {min(DISPLAY_LIMIT, len(lines))} 条")


def query_compound(name: str) -> None:
    print(f"【KEGG 查询】化合物：{name}")
    text = kegg_get(f"find/compound/{urllib.parse.quote(name)}")
    lines = [l for l in text.strip().splitlines() if l]
    if not lines:
        print("  未找到化合物")
        return
    cid = lines[0].split("\t")[0]
    print(f"  ID: {cid}")
    entry = kegg_get(f"get/{cid}")
    for line in entry.splitlines()[:15]:
        print(f"  {line}")


def query_map(keyword: str) -> None:
    print(f"【KEGG 查询】通路搜索：{keyword}")
    text = kegg_get(f"find/pathway/{urllib.parse.quote(keyword)}")
    lines = [l for l in text.strip().splitlines() if l and "hsa" in l]
    if not lines:
        print("  未找到通路")
        return
    for line in lines[:DISPLAY_LIMIT]:
        parts = line.split("\t")
        print(f"  {parts[0]}  {parts[1] if len(parts) > 1 else ''}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query KEGG REST API (academic use)")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("gene", help="Human gene entry").add_argument("symbol")
    sub.add_parser("pathway", help="Pathway entry").add_argument("pathway_id")
    sub.add_parser("disease", help="Search disease").add_argument("keyword")
    sub.add_parser("compound", help="Search compound").add_argument("name")
    sub.add_parser("map", help="Search pathway by keyword").add_argument("keyword")
    args = parser.parse_args()
    handlers = {
        "gene": lambda: query_gene(args.symbol),
        "pathway": lambda: query_pathway(args.pathway_id),
        "disease": lambda: query_disease(args.keyword),
        "compound": lambda: query_compound(args.name),
        "map": lambda: query_map(args.keyword),
    }
    try:
        handlers[args.mode]()
    except requests.RequestException as exc:
        print(f"API 请求失败：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
