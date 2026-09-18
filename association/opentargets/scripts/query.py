#!/usr/bin/env python3
"""Query OpenTargets Platform GraphQL API."""

from __future__ import annotations

import argparse
import json
import sys

import requests

API = "https://api.platform.opentargets.org/api/v4/graphql"
DISPLAY_LIMIT = 5


def graphql(query: str, variables: dict | None = None) -> dict:
    r = requests.post(API, json={"query": query, "variables": variables or {}}, timeout=60)
    r.raise_for_status()
    payload = r.json()
    if "errors" in payload:
        msgs = "; ".join(e.get("message", str(e)) for e in payload["errors"])
        raise RuntimeError(msgs)
    return payload.get("data") or {}


def resolve_ensembl(symbol: str) -> str | None:
    data = graphql(
        """query($q: String!) { search(queryString: $q, entityNames: ["target"]) {
          hits { id name description entity } } }""",
        {"q": symbol},
    )
    hits = (data.get("search") or {}).get("hits") or []
    for h in hits:
        if h.get("entity") == "target":
            return h.get("id")
    return None


def query_gene(symbol: str) -> None:
    print(f"【OpenTargets 查询】靶点/基因：{symbol}")
    eid = resolve_ensembl(symbol)
    if not eid:
        print("  未找到靶点")
        return
    data = graphql(
        """query($id: String!) { target(ensemblId: $id) {
          id approvedSymbol approvedName biotype
          tractability { label modality value }
          associatedDiseases(page: {index: 0, size: 5}) {
            count rows { disease { id name } score }
          }
        } }""",
        {"id": eid},
    )
    t = data.get("target") or {}
    print(f"  Ensembl ID: {t.get('id')}")
    print(f"  符号: {t.get('approvedSymbol')}  名称: {t.get('approvedName')}")
    print(f"  类型: {t.get('biotype')}")
    tract = [x for x in (t.get("tractability") or []) if x.get("value")]
    if tract:
        print(f"  成药性: {', '.join(x.get('label', '') for x in tract[:3])}")
    diseases = (t.get("associatedDiseases") or {}).get("rows") or []
    if diseases:
        print(f"\n  关联疾病（前 {DISPLAY_LIMIT} 个）:")
        for d in diseases[:DISPLAY_LIMIT]:
            disease = d.get("disease") or {}
            print(f"    {disease.get('name')}  分数: {d.get('score', 'N/A'):.3f}")


def query_disease(keyword: str) -> None:
    print(f"【OpenTargets 查询】疾病：{keyword}")
    data = graphql(
        """query($q: String!) { search(queryString: $q, entityNames: ["disease"]) {
          hits { id name description entity } } }""",
        {"q": keyword},
    )
    hits = (data.get("search") or {}).get("hits") or []
    if not hits:
        print("  未找到疾病")
        return
    for i, h in enumerate(hits[:DISPLAY_LIMIT], 1):
        print(f"  [{i}] {h.get('id')}  {h.get('name')}")
        if h.get("description"):
            print(f"      {h['description'][:120]}")


def query_variant(rsid: str) -> None:
    rs = rsid if rsid.startswith("rs") else f"rs{rsid}"
    print(f"【OpenTargets 查询】变异：{rs}")
    data = graphql(
        """query($id: String!) { variant(variantId: $id) {
          id rsIds chromosome position refAllele altAllele
          colocalisation(colocalisationMethod: "GWAS") { count }
        } }""",
        {"id": rs},
    )
    v = data.get("variant")
    if not v:
        data = graphql(
            """query($q: String!) { search(queryString: $q, entityNames: ["variant"]) {
              hits { id name description } } }""",
            {"q": rs},
        )
        hits = (data.get("search") or {}).get("hits") or []
        if hits:
            print(f"  匹配: {hits[0].get('id')}  {hits[0].get('name')}")
        else:
            print("  未找到变异")
        return
    print(f"  坐标: chr{v.get('chromosome')}:{v.get('position')} {v.get('refAllele')}>{v.get('altAllele')}")
    print(f"  rsIDs: {', '.join(v.get('rsIds') or [])}")


def query_drug(name: str) -> None:
    print(f"【OpenTargets 查询】药物：{name}")
    data = graphql(
        """query($q: String!) { search(queryString: $q, entityNames: ["drug"]) {
          hits { id name description entity } } }""",
        {"q": name},
    )
    hits = (data.get("search") or {}).get("hits") or []
    if not hits:
        print("  未找到药物")
        return
    for i, h in enumerate(hits[:DISPLAY_LIMIT], 1):
        print(f"  [{i}] {h.get('id')}  {h.get('name')}")


def query_target_disease(symbol: str, disease: str) -> None:
    print(f"【OpenTargets 查询】{symbol} ↔ {disease}")
    eid = resolve_ensembl(symbol)
    if not eid:
        print("  未找到靶点")
        return
    data = graphql(
        """query($q: String!) { search(queryString: $q, entityNames: ["disease"]) {
          hits { id name } } }""",
        {"q": disease},
    )
    hits = (data.get("search") or {}).get("hits") or []
    if not hits:
        print("  未找到疾病")
        return
    did = hits[0]["id"]
    assoc = graphql(
        """query($e: String!, $d: String!) {
          disease(efoId: $d) {
            id name
            associatedTargets(page: {index: 0, size: 20}) {
              rows { target { approvedSymbol } score datatypeScores { id score } }
            }
          }
        }""",
        {"e": eid, "d": did},
    )
    disease_data = assoc.get("disease") or {}
    print(f"  疾病: {disease_data.get('name')} ({did})")
    rows = (disease_data.get("associatedTargets") or {}).get("rows") or []
    for row in rows:
        if (row.get("target") or {}).get("approvedSymbol", "").upper() == symbol.upper():
            print(f"  关联分数: {row.get('score')}")
            for ds in row.get("datatypeScores") or []:
                print(f"    {ds.get('id')}: {ds.get('score')}")
            return
    print(f"  未在 top 关联中找到 {symbol}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query OpenTargets Platform")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("gene", help="Target/gene info").add_argument("symbol")
    sub.add_parser("disease", help="Search disease").add_argument("keyword")
    sub.add_parser("variant", help="Variant info").add_argument("rsid")
    sub.add_parser("drug", help="Search drug").add_argument("name")
    p = sub.add_parser("target", help="Target-disease association")
    p.add_argument("symbol")
    p.add_argument("disease")
    args = parser.parse_args()
    handlers = {
        "gene": lambda: query_gene(args.symbol),
        "disease": lambda: query_disease(args.keyword),
        "variant": lambda: query_variant(args.rsid),
        "drug": lambda: query_drug(args.name),
        "target": lambda: query_target_disease(args.symbol, args.disease),
    }
    try:
        handlers[args.mode]()
    except (requests.RequestException, RuntimeError) as exc:
        print(f"查询失败：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
