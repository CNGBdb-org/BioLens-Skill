#!/usr/bin/env python3
"""Query LOVD — HGVS validation, gene check, and UCSC Beacon for public LOVD instances."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse

import requests

LOVD_API = "https://api.lovd.nl/v2"
BEACON = "https://genome.ucsc.edu/cgi-bin/hgBeacon/query"
DISPLAY_LIMIT = 5


def lovd_get(path: str) -> dict:
    r = requests.get(f"{LOVD_API}{path}", timeout=60)
    r.raise_for_status()
    return r.json()


def query_gene(symbol: str) -> None:
    print(f"【LOVD 查询】基因验证：{symbol}")
    data = lovd_get(f"/checkGene/{urllib.parse.quote(symbol)}")
    for item in (data.get("data") or [])[:1]:
        print(f"  输入: {item.get('input')}")
        print(f"  有效: {item.get('valid')}")
        print(f"  HGNC ID: {(item.get('data') or {}).get('hgnc_id', 'N/A')}")
        corrected = item.get("corrected_values") or {}
        if corrected:
            print(f"  官方符号: {', '.join(corrected.keys())}")
    print("  全球 LOVD 变异搜索：使用 `coord` 或 `hgvs` + https://lovd.nl/3.0/search")


def query_hgvs(hgvs: str) -> None:
    print(f"【LOVD 查询】HGVS 验证：{hgvs}")
    data = lovd_get(f"/checkHGVS/{urllib.parse.quote(hgvs, safe='')}")
    for item in (data.get("data") or [])[:1]:
        print(f"  输入: {item.get('input')}")
        print(f"  类型: {item.get('identified_as_formatted', item.get('identified_as'))}")
        print(f"  HGVS 语法有效: {item.get('valid')}")
        inner = item.get("data") or {}
        if inner.get("position_start"):
            print(f"  位置: c.{inner.get('position_start')}  变异类型: {inner.get('type')}")
        corrected = item.get("corrected_values") or {}
        if corrected:
            print(f"  建议修正: {', '.join(corrected.keys())}")
        for code, msg in (item.get("warnings") or {}).items():
            print(f"  警告 [{code}]: {msg}")
    print("  序列级验证：https://variantvalidator.org")


def query_coord(chrom: str, pos: str, alt: str = "N") -> None:
    pos0 = int(pos) - 1
    print(f"【LOVD 查询】坐标 Beacon：chr{chrom}:{pos} (0-based={pos0})")
    r = requests.get(
        BEACON,
        params={"dataset": "lovd", "chromosome": chrom.replace("chr", ""), "position": pos0, "alternateBases": alt},
        timeout=30,
    )
    r.raise_for_status()
    try:
        result = r.json()
        exists = result.get("response", False)
        if isinstance(exists, str):
            exists = exists.lower() == "true"
    except json.JSONDecodeError:
        exists = r.text.strip().lower() == "true"
    print(f"  公共 LOVD 有记录: {'是' if exists else '否'}")
    if exists:
        print(f"  详情：https://lovd.nl/3.0/search （搜索 chr{chrom}:g.{pos}）")
    else:
        print("  未在公共 LOVD Beacon 命中；可能未收录或等位基因不匹配")


def query_check(hgvs: str) -> None:
    query_hgvs(hgvs)


def parse_region(region: str) -> tuple[str, str, str]:
    m = re.match(r"^(?:chr)?(\w+):g\.(\d+)([ACGTN>]+.*)?$", region.strip(), re.I)
    if m:
        alt = "N"
        if ">" in (m.group(3) or ""):
            parts = m.group(3).split(">")
            if len(parts) > 1 and parts[1]:
                alt = parts[1][0]
        return m.group(1), m.group(2), alt
    m2 = re.match(r"^(?:chr)?(\w+):(\d+)$", region.strip(), re.I)
    if m2:
        return m2.group(1), m2.group(2), "N"
    raise ValueError(f"无法解析区域：{region}")


def query_region(region: str) -> None:
    chrom, pos, alt = parse_region(region)
    query_coord(chrom, pos, alt)


def main() -> None:
    parser = argparse.ArgumentParser(description="Query LOVD APIs and public Beacon")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("gene", help="Validate gene symbol").add_argument("symbol")
    sub.add_parser("hgvs", help="Validate HGVS nomenclature").add_argument("hgvs")
    sub.add_parser("check", help="Alias for hgvs").add_argument("hgvs")
    p = sub.add_parser("coord", help="Check position in public LOVDs (Beacon)")
    p.add_argument("chrom")
    p.add_argument("pos")
    p.add_argument("alt", nargs="?", default="N")
    sub.add_parser("region", help="Region in HGVS genomic format").add_argument("region")
    args = parser.parse_args()
    handlers = {
        "gene": lambda: query_gene(args.symbol),
        "hgvs": lambda: query_hgvs(args.hgvs),
        "check": lambda: query_check(args.hgvs),
        "coord": lambda: query_coord(args.chrom, args.pos, args.alt),
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
