#!/usr/bin/env python3
"""Query NCBI RefSeq via E-utilities — gene, transcript, protein, region."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time

import requests

BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
API_DELAY = 0.34
DISPLAY_LIMIT = 5


def esearch(db: str, term: str, retmax: int = DISPLAY_LIMIT) -> tuple[list[str], str]:
    time.sleep(API_DELAY)
    r = requests.get(
        f"{BASE}/esearch.fcgi",
        params={"db": db, "term": term, "retmode": "json", "retmax": retmax},
        timeout=30,
    )
    r.raise_for_status()
    result = r.json().get("esearchresult", {})
    return result.get("idlist", []), result.get("count", "0")


def esummary(db: str, ids: list[str]) -> list[dict]:
    if not ids:
        return []
    time.sleep(API_DELAY)
    r = requests.get(
        f"{BASE}/esummary.fcgi",
        params={"db": db, "id": ",".join(ids), "retmode": "json"},
        timeout=30,
    )
    r.raise_for_status()
    result = r.json().get("result", {})
    uids = result.get("uids", [])
    return [result[uid] for uid in uids if uid in result]


def parse_region(region: str) -> str:
    m = re.match(r"^(?:chr)?(\w+):(\d+)-(\d+)$", region.strip(), re.I)
    if m:
        return f"{m.group(1)}[{m.group(2)}:{m.group(3)}]"
    parts = region.split()
    if len(parts) == 3:
        return f"{parts[0].replace('chr', '')}[{parts[1]}:{parts[2]}]"
    raise ValueError(f"无法解析区域：{region}")


def print_gene_records(records: list[dict], total: str) -> None:
    for i, rec in enumerate(records, 1):
        print(f"\n===== 结果 {i} =====")
        print(f"  Gene ID: {rec.get('uid', rec.get('id', 'N/A'))}")
        print(f"  符号: {rec.get('name', 'N/A')}")
        print(f"  描述: {rec.get('description', 'N/A')}")
        print(f"  染色体: {rec.get('chromosome', 'N/A')}")
        loc = rec.get("genomicinfo") or rec.get("genomic_info") or []
        if loc and isinstance(loc, list):
            g = loc[0]
            print(f"  坐标: chr{g.get('chraccver', g.get('chracc', 'N/A')).split('.')[0].replace('NC_0000', '').replace('NC_000', '')}:"
                  f"{g.get('chrstart', 'N/A')}-{g.get('chrstop', 'N/A')}")
        print(f"  类型: {rec.get('genetic_source', rec.get('source', 'N/A'))}")
    print(f"\n共检索到 {total} 条，展示前 {len(records)} 条")


def query_gene(symbol: str) -> None:
    print(f"【RefSeq 查询】基因：{symbol}")
    term = f"{symbol}[gene] AND homo sapiens[orgn]"
    ids, total = esearch("gene", term)
    records = esummary("gene", ids)
    if not records:
        print("  未找到结果")
        return
    print_gene_records(records, total)


def query_transcript(acc: str) -> None:
    print(f"【RefSeq 查询】转录本：{acc}")
    ids, _ = esearch("nuccore", acc)
    if not ids:
        print("  未找到转录本")
        return
    records = esummary("nuccore", ids[:1])
    rec = records[0]
    print(f"  Accession: {rec.get('accessionversion', rec.get('caption', 'N/A'))}")
    print(f"  标题: {rec.get('title', 'N/A')}")
    print(f"  长度: {rec.get('slen', 'N/A')} bp")
    print(f"  更新: {rec.get('updatedate', 'N/A')}")


def query_protein(acc: str) -> None:
    print(f"【RefSeq 查询】蛋白：{acc}")
    ids, _ = esearch("protein", acc)
    if not ids:
        print("  未找到蛋白")
        return
    records = esummary("protein", ids[:1])
    rec = records[0]
    print(f"  Accession: {rec.get('accessionversion', 'N/A')}")
    print(f"  标题: {rec.get('title', 'N/A')}")
    print(f"  长度: {rec.get('slen', 'N/A')} aa")


def query_region(region: str) -> None:
    chrom_range = parse_region(region)
    print(f"【RefSeq 查询】区域：{region}")
    term = f"{chrom_range}[Gene]"
    ids, total = esearch("gene", term, retmax=DISPLAY_LIMIT)
    records = esummary("gene", ids)
    if not records:
        print("  未找到基因")
        return
    print_gene_records(records, total)


def main() -> None:
    parser = argparse.ArgumentParser(description="Query NCBI RefSeq")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("gene", help="Gene by symbol").add_argument("symbol")
    sub.add_parser("transcript", help="Transcript by accession").add_argument("accession")
    sub.add_parser("protein", help="Protein by accession").add_argument("accession")
    sub.add_parser("region", help="Genes in region").add_argument("region")
    args = parser.parse_args()
    handlers = {
        "gene": lambda: query_gene(args.symbol),
        "transcript": lambda: query_transcript(args.accession),
        "protein": lambda: query_protein(args.accession),
        "region": lambda: query_region(args.region),
    }
    try:
        handlers[args.mode]()
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        sys.exit(1)
    except requests.RequestException as exc:
        print(f"API 请求失败：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
