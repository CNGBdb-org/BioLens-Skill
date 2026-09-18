#!/usr/bin/env python3
"""Query GWAS Catalog REST API — rsID, trait, gene, study."""

from __future__ import annotations

import argparse
import json
import sys

import requests

BASE = "https://www.ebi.ac.uk/gwas/rest/api"
DISPLAY_LIMIT = 5


def api_get(path: str, params: dict | None = None) -> dict:
    r = requests.get(f"{BASE}{path}", params=params, timeout=60)
    r.raise_for_status()
    return r.json() if r.content else {}


def fmt_pvalue(assoc: dict) -> str:
    m = assoc.get("pvalueMantissa")
    e = assoc.get("pvalueExponent")
    if m is not None and e is not None:
        return f"{m}e{e}"
    return "N/A"


def query_rsid(rsid: str) -> None:
    rs = rsid if rsid.startswith("rs") else f"rs{rsid}"
    print(f"【GWAS Catalog 查询】rsID：{rs}")
    snp = api_get(f"/singleNucleotidePolymorphisms/{rs}")
    print(f"  功能类别: {snp.get('functionalClass', 'N/A')}")
    locs = snp.get("locations") or []
    for loc in locs[:2]:
        print(f"  坐标: chr{loc.get('chromosomeName')}:{loc.get('chromosomePosition')}")
    data = api_get("/associations/search/findByRsId", {"rsId": rs, "size": DISPLAY_LIMIT})
    assocs = (data.get("_embedded") or {}).get("associations") or []
    if not assocs:
        print("  未找到 GWAS 关联")
        return
    for i, a in enumerate(assocs, 1):
        trait = (a.get("efoTraits") or [{}])[0].get("trait", "N/A") if a.get("efoTraits") else "N/A"
        if isinstance(a.get("efoTraits"), list) and a["efoTraits"]:
            trait = a["efoTraits"][0].get("trait", trait)
        loci = a.get("loci") or [{}]
        risk = ""
        if loci and loci[0].get("strongestRiskAlleles"):
            risk = loci[0]["strongestRiskAlleles"][0].get("riskAlleleName", "")
        print(f"\n  [{i}] 性状: {trait}")
        print(f"      p值: {fmt_pvalue(a)}  OR: {a.get('orPerCopyNum', 'N/A')}  风险等位基因: {risk}")
        study = a.get("study") or {}
        if isinstance(study, dict):
            print(f"      研究: {study.get('publicationTitle', 'N/A')[:80]}")
    print(f"\n展示前 {len(assocs)} 条关联")


def query_trait(keyword: str) -> None:
    print(f"【GWAS Catalog 查询】性状：{keyword}")
    data = api_get("/studies/search/findByDiseaseTrait", {"diseaseTrait": keyword, "size": DISPLAY_LIMIT})
    studies = (data.get("_embedded") or {}).get("studies") or []
    if not studies:
        print("  未找到相关研究")
        return
    for i, s in enumerate(studies, 1):
        print(f"\n  [{i}] {s.get('diseaseTrait', 'N/A')}")
        print(f"      样本量: {s.get('initialSampleSize', 'N/A')}")
        print(f"      PubMed: {s.get('pubmedId', 'N/A')}")
        print(f"      研究 ID: {s.get('accessionId', 'N/A')}")
    total = (data.get("page") or {}).get("totalElements", len(studies))
    print(f"\n共 {total} 个研究，展示前 {len(studies)} 个")


def query_gene(symbol: str) -> None:
    print(f"【GWAS Catalog 查询】基因：{symbol}")
    data = api_get("/singleNucleotidePolymorphisms/search/findByGene", {"geneName": symbol, "size": DISPLAY_LIMIT})
    snps = (data.get("_embedded") or {}).get("singleNucleotidePolymorphisms") or []
    if not snps:
        print("  未找到 SNP")
        return
    for i, s in enumerate(snps, 1):
        rs = s.get("rsId", "N/A")
        locs = s.get("locations") or [{}]
        pos = locs[0].get("chromosomePosition", "N/A") if locs else "N/A"
        print(f"  [{i}] {rs}  chr{locs[0].get('chromosomeName', '?')}:{pos}  {s.get('functionalClass', '')}")
    print(f"\n展示前 {len(snps)} 条")


def query_study(study_id: str) -> None:
    print(f"【GWAS Catalog 查询】研究：{study_id}")
    sid = study_id if study_id.startswith("GCST") else study_id
    data = api_get(f"/studies/{sid}")
    print(f"  性状: {data.get('diseaseTrait', 'N/A')}")
    print(f"  样本量: {data.get('initialSampleSize', 'N/A')}")
    print(f"  PubMed: {data.get('pubmedId', 'N/A')}")
    print(f"  平台: {data.get('genotypingTechnology', 'N/A')}")
    print(f"  SNP 数: {data.get('snpCount', 'N/A')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query GWAS Catalog")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("rsid", help="Associations for rsID").add_argument("rsid")
    sub.add_parser("trait", help="Studies by disease/trait").add_argument("keyword")
    sub.add_parser("gene", help="SNPs mapped to gene").add_argument("gene")
    sub.add_parser("study", help="Study details").add_argument("study_id")
    args = parser.parse_args()
    handlers = {
        "rsid": lambda: query_rsid(args.rsid),
        "trait": lambda: query_trait(args.keyword),
        "gene": lambda: query_gene(args.gene),
        "study": lambda: query_study(args.study_id),
    }
    try:
        handlers[args.mode]()
    except requests.RequestException as exc:
        print(f"API 请求失败：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
