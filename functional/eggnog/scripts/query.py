#!/usr/bin/env python3
"""Query eggNOG — gene ortholog groups via UniProt crossrefs and eggNOG API."""

from __future__ import annotations

import argparse
import json
import sys

import requests

UNIPROT = "https://rest.uniprot.org"
EGGNOG_API = "http://eggnogapi5.embl.de/nog_data/json"
DISPLAY_LIMIT = 5


def uniprot_search_gene(symbol: str) -> list[dict]:
    r = requests.get(
        f"{UNIPROT}/uniprotkb/search",
        params={"query": f"gene:{symbol} AND organism_id:9606 AND reviewed:true", "format": "json", "size": 3},
        timeout=60,
    )
    r.raise_for_status()
    results = r.json().get("results") or []
    if not results:
        r = requests.get(
            f"{UNIPROT}/uniprotkb/search",
            params={"query": f"gene:{symbol} AND organism_id:9606", "format": "json", "size": 3},
            timeout=60,
        )
        r.raise_for_status()
        results = r.json().get("results") or []
    return results


def get_eggnog_ids(entry: dict) -> list[str]:
    return [x["id"] for x in entry.get("uniProtKBCrossReferences") or [] if x.get("database") == "eggNOG"]


def fetch_og_json(og_id: str, attribute: str) -> dict:
    r = requests.get(f"{EGGNOG_API}/{attribute}/{og_id}", timeout=60)
    r.raise_for_status()
    return r.json()


def query_gene(symbol: str) -> None:
    print(f"【eggNOG 查询】基因：{symbol}")
    results = uniprot_search_gene(symbol)
    if not results:
        print("  未找到 UniProt 条目")
        return
    entry = results[0]
    print(f"  UniProt: {entry.get('primaryAccession')}  {entry.get('uniProtkbId')}")
    ogs = get_eggnog_ids(entry)
    if not ogs:
        print("  未找到 eggNOG 直系同源组")
        return
    for og in ogs:
        print(f"  eggNOG OG: {og}")
        try:
            data = fetch_og_json(og, "go_terms")
            go_terms = data.get("go_terms") or {}
            for category, terms in go_terms.items():
                print(f"\n  {category}（前 3 个）:")
                for t in (terms or [])[:3]:
                    print(f"    {t[0]}  {t[1]}  (freq={t[4]}%)")
        except requests.RequestException as exc:
            print(f"  OG 详情获取失败：{exc}")


def query_og(og_id: str) -> None:
    print(f"【eggNOG 查询】直系同源组：{og_id}")
    for attr in ("go_terms", "domains"):
        try:
            data = fetch_og_json(og_id, attr)
            print(f"\n  === {attr} ===")
            if attr == "go_terms":
                for cat, terms in (data.get("go_terms") or {}).items():
                    print(f"  {cat}:")
                    for t in (terms or [])[:DISPLAY_LIMIT]:
                        print(f"    {t[0]}  {t[1]}")
            elif attr == "domains":
                for d in (data.get("domains") or [])[:DISPLAY_LIMIT]:
                    print(f"    {d}")
        except requests.RequestException as exc:
            print(f"  {attr} 获取失败：{exc}")


def query_ortholog(symbol: str) -> None:
    print(f"【eggNOG 查询】同源信息：{symbol}")
    results = uniprot_search_gene(symbol)
    if not results:
        print("  未找到")
        return
    for entry in results[:DISPLAY_LIMIT]:
        acc = entry.get("primaryAccession")
        ogs = get_eggnog_ids(entry)
        gene = (entry.get("genes") or [{}])[0].get("geneName", {}).get("value", symbol)
        print(f"  {acc}  {gene}  eggNOG: {', '.join(ogs) or 'N/A'}")


def query_function(symbol: str) -> None:
    print(f"【eggNOG 查询】功能注释：{symbol}")
    results = uniprot_search_gene(symbol)
    if not results:
        print("  未找到")
        return
    ogs = get_eggnog_ids(results[0])
    if not ogs:
        print("  无 eggNOG OG")
        return
    data = fetch_og_json(ogs[0], "go_terms")
    for cat, terms in (data.get("go_terms") or {}).items():
        print(f"\n  {cat}:")
        for t in (terms or [])[:DISPLAY_LIMIT]:
            print(f"    {t[0]}  {t[1]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query eggNOG ortholog groups")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("gene", help="Gene to eggNOG OG").add_argument("symbol")
    sub.add_parser("og", help="Ortholog group details").add_argument("og_id")
    sub.add_parser("ortholog", help="List eggNOG IDs for gene").add_argument("symbol")
    sub.add_parser("function", help="GO terms from OG").add_argument("symbol")
    args = parser.parse_args()
    handlers = {
        "gene": lambda: query_gene(args.symbol),
        "og": lambda: query_og(args.og_id),
        "ortholog": lambda: query_ortholog(args.symbol),
        "function": lambda: query_function(args.symbol),
    }
    try:
        handlers[args.mode]()
    except requests.RequestException as exc:
        print(f"API 请求失败：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
