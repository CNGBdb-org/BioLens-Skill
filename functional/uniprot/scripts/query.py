#!/usr/bin/env python3
"""Query UniProt REST API — gene, protein, function, disease."""

from __future__ import annotations

import argparse
import json
import sys

import requests

BASE = "https://rest.uniprot.org"
DISPLAY_LIMIT = 5


def search(query: str, size: int = DISPLAY_LIMIT) -> list[dict]:
    r = requests.get(
        f"{BASE}/uniprotkb/search",
        params={"query": query, "format": "json", "size": size},
        timeout=60,
    )
    r.raise_for_status()
    return r.json().get("results") or []


def get_entry(accession: str) -> dict:
    r = requests.get(f"{BASE}/uniprotkb/{accession}", params={"format": "json"}, timeout=60)
    r.raise_for_status()
    return r.json()


def fmt_genes(entry: dict) -> str:
    genes = entry.get("genes") or []
    names = []
    for g in genes:
        for n in g.get("geneName", {}).get("value", ""), *(x.get("value") for x in g.get("synonyms") or []):
            if n:
                names.append(n)
    return ", ".join(names[:5]) or "N/A"


def fmt_function(entry: dict) -> str:
    comments = entry.get("comments") or []
    for c in comments:
        if c.get("commentType") == "FUNCTION":
            texts = c.get("texts") or []
            if texts:
                return texts[0].get("value", "N/A")
    return "N/A"


def fmt_diseases(entry: dict) -> list[str]:
    out = []
    for c in entry.get("comments") or []:
        if c.get("commentType") == "DISEASE":
            d = c.get("disease") or {}
            name = d.get("diseaseId") or d.get("description") or "N/A"
            out.append(name)
    return out


def print_entry(entry: dict, idx: int | None = None) -> None:
    prefix = f"===== 结果 {idx} =====" if idx else "===== 详情 ====="
    print(prefix)
    print(f"  Accession: {entry.get('primaryAccession', 'N/A')}")
    print(f"  ID: {entry.get('uniProtkbId', 'N/A')}")
    print(f"  基因: {fmt_genes(entry)}")
    print(f"  蛋白名: {entry.get('proteinDescription', {}).get('recommendedName', {}).get('fullName', {}).get('value', 'N/A')}")
    seq = entry.get("sequence") or {}
    print(f"  长度: {seq.get('length', 'N/A')} aa")
    xrefs = entry.get("uniProtKBCrossReferences") or []
    ensembl = [x["id"] for x in xrefs if x.get("database") == "Ensembl"]
    if ensembl:
        print(f"  Ensembl: {', '.join(ensembl[:3])}")
    print(f"  功能: {fmt_function(entry)[:200]}")
    diseases = fmt_diseases(entry)
    if diseases:
        print(f"  疾病关联: {', '.join(diseases[:5])}")


def query_gene(symbol: str) -> None:
    print(f"【UniProt 查询】基因：{symbol}")
    results = search(f"gene:{symbol} AND organism_id:9606")
    if not results:
        print("  未找到结果")
        return
    for i, entry in enumerate(results[:DISPLAY_LIMIT], 1):
        print_entry(entry, i)
    print(f"\n共 {len(results)} 条，展示前 {min(DISPLAY_LIMIT, len(results))} 条")


def query_protein(accession: str) -> None:
    print(f"【UniProt 查询】蛋白：{accession}")
    entry = get_entry(accession)
    print_entry(entry)


def query_id(identifier: str) -> None:
    print(f"【UniProt 查询】ID：{identifier}")
    results = search(f"(accession:{identifier}) OR (id:{identifier}) OR (gene:{identifier}) AND organism_id:9606", size=3)
    if not results:
        print("  未找到结果")
        return
    print_entry(results[0])


def query_function(symbol: str) -> None:
    print(f"【UniProt 查询】功能注释：{symbol}")
    results = search(f"gene:{symbol} AND organism_id:9606 AND reviewed:true", size=1)
    if not results:
        results = search(f"gene:{symbol} AND organism_id:9606", size=1)
    if not results:
        print("  未找到结果")
        return
    entry = results[0]
    print(f"  Accession: {entry.get('primaryAccession')}")
    print(f"  功能: {fmt_function(entry)}")
    for c in entry.get("comments") or []:
        if c.get("commentType") in ("SUBCELLULAR LOCATION", "CATALYTIC ACTIVITY", "PATHWAY"):
            texts = (c.get("texts") or [{}])[0].get("value", "")
            if texts:
                print(f"  {c['commentType']}: {texts[:150]}")


def query_disease(keyword: str) -> None:
    print(f"【UniProt 查询】疾病关联：{keyword}")
    results = search(f"(disease:{keyword}) AND organism_id:9606")
    if not results:
        print("  未找到结果")
        return
    for i, entry in enumerate(results[:DISPLAY_LIMIT], 1):
        print_entry(entry, i)
    print(f"\n共 {len(results)} 条，展示前 {min(DISPLAY_LIMIT, len(results))} 条")


def emit_json(data: dict) -> None:
    print(json.dumps(data, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser(description="Query UniProt REST API")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("gene", help="Search by gene symbol").add_argument("gene")
    sub.add_parser("protein", help="Get entry by accession").add_argument("accession")
    sub.add_parser("id", help="Lookup by accession/ID/gene").add_argument("identifier")
    sub.add_parser("function", help="Functional annotation").add_argument("gene")
    sub.add_parser("disease", help="Proteins linked to disease").add_argument("keyword")
    args = parser.parse_args()
    handlers = {
        "gene": lambda: query_gene(args.gene),
        "protein": lambda: query_protein(args.accession),
        "id": lambda: query_id(args.identifier),
        "function": lambda: query_function(args.gene),
        "disease": lambda: query_disease(args.keyword),
    }
    try:
        handlers[args.mode]()
    except requests.RequestException as exc:
        print(f"API 请求失败：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
