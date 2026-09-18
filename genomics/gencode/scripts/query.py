#!/usr/bin/env python3
"""Query GENCODE annotations via Ensembl REST API (GENCODE is hosted on Ensembl)."""

from __future__ import annotations

import argparse
import re
import sys

import requests

BASE = "https://rest.ensembl.org"
SPECIES = "homo_sapiens"
DISPLAY_LIMIT = 5


def api_get(path: str, params: dict | None = None) -> dict | list:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    r = requests.get(f"{BASE}{path}", params=params, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json() if r.content else {}


def parse_region(region: str) -> tuple[str, int, int]:
    m = re.match(r"^(?:chr)?(\w+):(\d+)-(\d+)$", region.strip(), re.I)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(3))
    parts = region.split()
    if len(parts) == 3:
        return parts[0].replace("chr", ""), int(parts[1]), int(parts[2])
    raise ValueError(f"无法解析区域：{region}")


def is_gencode_source(entry: dict) -> bool:
    src = (entry.get("source") or entry.get("logic_name") or "").lower()
    return "gencode" in src or "havana" in src or "ensembl" in src


def query_gene(symbol: str) -> None:
    print(f"【GENCODE 查询】基因：{symbol}")
    data = api_get(f"/lookup/symbol/{SPECIES}/{symbol}", {"expand": 1})
    print(f"  GENCODE/Ensembl ID: {data.get('id')}")
    print(f"  名称: {data.get('display_name')}")
    print(f"  描述: {data.get('description', 'N/A')}")
    print(f"  类型: {data.get('biotype')}")
    print(f"  坐标: chr{data.get('seq_region_name')}:{data.get('start')}-{data.get('end')} (GENCODE via Ensembl)")
    print(f"  版本: {data.get('version', 'N/A')}")
    children = data.get("Transcript") or []
    if isinstance(children, dict):
        children = list(children.values())
    gencode_tx = [t for t in children if is_gencode_source(t)] or children
    print(f"\n  转录本（前 {DISPLAY_LIMIT} 个）:")
    for tx in gencode_tx[:DISPLAY_LIMIT]:
        print(f"    {tx.get('id')}  {tx.get('biotype')}  v{tx.get('version', '?')}  "
              f"{tx.get('start')}-{tx.get('end')}  {tx.get('logic_name', '')}")


def query_transcript(tx_id: str) -> None:
    print(f"【GENCODE 查询】转录本：{tx_id}")
    data = api_get(f"/lookup/id/{tx_id}", {"expand": 1})
    print(f"  ID: {data.get('id')}")
    print(f"  基因: {data.get('Parent') or data.get('display_name', 'N/A')}")
    print(f"  类型: {data.get('biotype')}")
    print(f"  坐标: chr{data.get('seq_region_name')}:{data.get('start')}-{data.get('end')}")
    print(f"  长度: {data.get('end', 0) - data.get('start', 0)} bp")
    exons = data.get("Exon") or []
    if isinstance(exons, dict):
        exons = list(exons.values())
    print(f"  外显子数: {len(exons)}")


def query_version() -> None:
    print("【GENCODE 查询】当前版本信息")
    info = api_get("/info/data/")
    print(f"  Ensembl 版本: {info.get('release')}")
    print(f"  API 版本: {info.get('api_version')}")
    print(f"  组装: {info.get('assembly')}")
    print("  说明: GENCODE 注释通过 Ensembl REST API 提供，与 GENCODE 官网同步发布")


def query_region(region: str) -> None:
    chrom, start, end = parse_region(region)
    print(f"【GENCODE 查询】区域：chr{chrom}:{start}-{end}")
    data = api_get(
        f"/overlap/region/{SPECIES}/{chrom}:{start}-{end}",
        {"feature": "transcript", "biotype": "protein_coding"},
    )
    feats = data if isinstance(data, list) else []
    if not feats:
        print("  未找到转录本")
        return
    for i, t in enumerate(feats[:DISPLAY_LIMIT], 1):
        print(f"  [{i}] {t.get('id')}  {t.get('external_name', t.get('display_name', ''))}  "
              f"{t.get('biotype')}  {t.get('start')}-{t.get('end')}")
    print(f"\n共 {len(feats)} 条，展示前 {min(DISPLAY_LIMIT, len(feats))} 条")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query GENCODE via Ensembl API")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("gene", help="Gene annotation").add_argument("symbol")
    sub.add_parser("transcript", help="Transcript details").add_argument("transcript_id")
    sub.add_parser("version", help="GENCODE/Ensembl release info")
    sub.add_parser("region", help="Transcripts in region").add_argument("region")
    args = parser.parse_args()
    handlers = {
        "gene": lambda: query_gene(args.symbol),
        "transcript": lambda: query_transcript(args.transcript_id),
        "version": lambda: query_version(),
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
