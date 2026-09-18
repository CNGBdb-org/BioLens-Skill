#!/usr/bin/env python3
"""Query Dfam — repetitive DNA families and region annotations."""

from __future__ import annotations

import argparse
import re
import sys

import requests

BASE = "https://dfam.org/api"
DISPLAY_LIMIT = 5


def api_get(path: str, params: dict | None = None) -> dict:
    r = requests.get(f"{BASE}{path}", params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def query_family(name: str) -> None:
    print(f"【Dfam 查询】重复元件家族：{name}")
    data = api_get("/families", {"name": name, "limit": DISPLAY_LIMIT})
    results = data.get("results") or []
    if not results:
        data = api_get("/families", {"accession": name, "limit": 1})
        results = data.get("results") or []
    if not results:
        print("  未找到家族")
        return
    for i, fam in enumerate(results, 1):
        print(f"\n  [{i}] {fam.get('accession')}  {fam.get('name')}")
        print(f"      版本: v{fam.get('version', 'N/A')}")
        print(f"      标题: {fam.get('title', 'N/A')}")
        desc = fam.get("description") or ""
        if desc:
            print(f"      描述: {desc[:200]}...")
        print(f"      类型: {fam.get('repeat_type', fam.get('type', 'N/A'))}")
        print(f"      物种: {fam.get('species', 'N/A')}")


def query_search(keyword: str) -> None:
    print(f"【Dfam 查询】搜索：{keyword}")
    data = api_get("/families", {"name": keyword, "limit": DISPLAY_LIMIT})
    results = data.get("results") or []
    total = data.get("total_count", len(results))
    if not results:
        print("  未找到结果")
        return
    for i, fam in enumerate(results, 1):
        print(f"  [{i}] {fam.get('accession')}  {fam.get('name')}  {fam.get('title', '')[:60]}")
    print(f"\n共 {total} 条，展示前 {len(results)} 条")


def query_model(accession: str) -> None:
    print(f"【Dfam 查询】HMM 模型：{accession}")
    acc = accession if accession.startswith("DF") else accession
    try:
        data = api_get(f"/families/{acc}")
    except requests.HTTPError:
        data = api_get("/families", {"accession": acc, "limit": 1})
        results = data.get("results") or []
        if not results:
            print("  未找到")
            return
        data = results[0]
    print(f"  Accession: {data.get('accession')}")
    print(f"  名称: {data.get('name')}")
    print(f"  长度: {data.get('length', 'N/A')} bp")
    print(f"  Gathering threshold: {data.get('gathering_threshold', 'N/A')}")
    print(f"  分类: {data.get('repeat_type', 'N/A')}")


def query_repeat(keyword: str) -> None:
    print(f"【Dfam 查询】重复类型：{keyword}")
    data = api_get("/families", {"repeat_type": keyword, "limit": DISPLAY_LIMIT})
    results = data.get("results") or []
    if not results:
        data = api_get("/families", {"name": keyword, "limit": DISPLAY_LIMIT})
        results = data.get("results") or []
    if not results:
        print("  未找到")
        return
    for i, fam in enumerate(results, 1):
        print(f"  [{i}] {fam.get('accession')}  {fam.get('name')}  {fam.get('repeat_type', '')}")


def query_region(region: str) -> None:
    print(f"【Dfam 查询】区域：{region}")
    print("  说明: Dfam 公共 API 不直接提供基因组坐标区间查询。")
    print("  建议: 使用 RepeatMasker/UCSC RepeatMasker track，或 Dfam 官网 Genome Browser。")
    m = re.match(r"^(?:chr)?(\w+):(\d+)-(\d+)$", region.strip(), re.I)
    if m:
        print(f"  输入区域: chr{m.group(1)}:{m.group(2)}-{m.group(3)}")
        print("  联动: ucsc skill → track RepeatMasker <region>")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query Dfam repetitive element database")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("family", help="Family by name/accession").add_argument("name")
    sub.add_parser("search", help="Search families").add_argument("keyword")
    sub.add_parser("model", help="HMM model details").add_argument("accession")
    sub.add_parser("repeat", help="Families by repeat type").add_argument("keyword")
    sub.add_parser("region", help="Region guidance (no direct API)").add_argument("region")
    args = parser.parse_args()
    handlers = {
        "family": lambda: query_family(args.name),
        "search": lambda: query_search(args.keyword),
        "model": lambda: query_model(args.accession),
        "repeat": lambda: query_repeat(args.keyword),
        "region": lambda: query_region(args.region),
    }
    try:
        handlers[args.mode]()
    except requests.RequestException as exc:
        print(f"API 请求失败：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
