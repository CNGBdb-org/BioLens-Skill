#!/usr/bin/env python3
"""Query DGV / DGVa copy-number variants via Ensembl REST API."""

from __future__ import annotations

import argparse
import re
import sys

import requests

ENSEMBL = "https://rest.ensembl.org"
SPECIES = "homo_sapiens"
DISPLAY_LIMIT = 5


def api_get(path: str, params: dict | None = None) -> list | dict:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    r = requests.get(f"{ENSEMBL}{path}", params=params, headers=headers, timeout=120)
    r.raise_for_status()
    return r.json() if r.content else []


def parse_region(region: str) -> tuple[str, int, int]:
    m = re.match(r"^(?:chr)?(\w+):(\d+)-(\d+)$", region.strip(), re.I)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(3))
    parts = region.split()
    if len(parts) == 3:
        return parts[0].replace("chr", ""), int(parts[1]), int(parts[2])
    raise ValueError(f"无法解析区域：{region}")


def filter_overlap(items: list[dict], start: int, end: int, max_sv_size: int | None = None) -> list[dict]:
    region_len = max(end - start, 1)
    if max_sv_size is None:
        max_sv_size = max(5_000_000, region_len * 20)
    out = []
    for item in items:
        s = int(item.get("start", 0))
        e = int(item.get("end", 0))
        if s > end or e < start:
            continue
        sv_len = e - s
        if sv_len > max_sv_size:
            continue
        out.append(item)
    out.sort(key=lambda x: (int(x.get("end", 0)) - int(x.get("start", 0))))
    return out


def fmt_sv(item: dict) -> None:
    print(f"  ID: {item.get('id', 'N/A')}")
    print(f"  类型: {item.get('sv_type', item.get('variant_class', 'N/A'))}")
    print(f"  坐标: chr{item.get('seq_region_name')}:{item.get('start')}-{item.get('end')}")
    sig = item.get("clinical_significance") or item.get("clin_sig")
    if sig:
        print(f"  临床意义: {sig}")
    studies = item.get("study") or item.get("studies")
    if studies:
        print(f"  研究: {studies}")


def query_region(region: str) -> None:
    chrom, start, end = parse_region(region)
    print(f"【DGV 查询】区域 CNV：chr{chrom}:{start}-{end}")
    data = api_get(
        f"/overlap/region/{SPECIES}/{chrom}:{start}-{end}",
        {"feature": "structural_variation", "source": "DGVa"},
    )
    items = filter_overlap(data if isinstance(data, list) else [], start, end)
    if not items:
        data2 = api_get(
            f"/overlap/region/{SPECIES}/{chrom}:{start}-{end}",
            {"feature": "structural_variation", "source": "DGV"},
        )
        items = filter_overlap(data2 if isinstance(data2, list) else [], start, end)
    if not items:
        print("  该区域未找到 DGV/DGVa CNV")
        return
    for i, item in enumerate(items[:DISPLAY_LIMIT], 1):
        print(f"\n  [{i}]")
        fmt_sv(item)
    print(f"\n共 {len(items)} 条，展示前 {min(DISPLAY_LIMIT, len(items))} 条")
    print("  说明：DGV 已整合至 DGVa/dbVar；完整 CNV 注释可联动 clinvar/clinicalgenome")


def query_gene(symbol: str) -> None:
    print(f"【DGV 查询】基因 CNV：{symbol}")
    gene = api_get(f"/lookup/symbol/{SPECIES}/{symbol}")
    gid = gene.get("id")
    if not gid:
        print("  未找到基因")
        return
    start, end = gene.get("start", 0), gene.get("end", 0)
    chrom = gene.get("seq_region_name")
    print(f"  基因: {gene.get('display_name')}  {gid}")
    print(f"  坐标: chr{chrom}:{start}-{end}")
    data = api_get(
        f"/overlap/region/{SPECIES}/{chrom}:{start}-{end}",
        {"feature": "structural_variation", "source": "DGVa"},
    )
    items = filter_overlap(data if isinstance(data, list) else [], start, end)
    if not items:
        print("  基因区域未找到 DGV CNV")
        return
    for i, item in enumerate(items[:DISPLAY_LIMIT], 1):
        print(f"\n  [{i}] {item.get('id')}  {item.get('sv_type', 'CNV')}  "
              f"chr{item.get('seq_region_name')}:{item.get('start')}-{item.get('end')}")
    print(f"\n共 {len(items)} 条，展示前 {min(DISPLAY_LIMIT, len(items))} 条")


def query_id(nsv_id: str) -> None:
    nid = nsv_id if nsv_id.startswith("nsv") else f"nsv{nsv_id}"
    print(f"【DGV 查询】变异 ID：{nid}")
    try:
        data = api_get(f"/variation/{SPECIES}/{nid}")
    except requests.HTTPError:
        print("  未找到该 DGV 变异 ID")
        return
    if isinstance(data, list):
        data = data[0] if data else {}
    print(f"  名称: {data.get('name', nid)}")
    mappings = data.get("mappings") or []
    for m in mappings[:2]:
        print(f"  坐标: chr{m.get('seq_region_name')}:{m.get('start')}-{m.get('end')} ({m.get('assembly_name')})")
    print(f"  类型: {data.get('variant_class', data.get('sv_type', 'N/A'))}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query DGV/DGVa copy-number variants")
    sub = parser.add_subparsers(dest="mode", required=True)
    sub.add_parser("region", help="CNVs overlapping region").add_argument("region")
    sub.add_parser("gene", help="CNVs in gene locus").add_argument("symbol")
    sub.add_parser("id", help="Lookup by nsv ID").add_argument("nsv_id")
    args = parser.parse_args()
    handlers = {
        "region": lambda: query_region(args.region),
        "gene": lambda: query_gene(args.symbol),
        "id": lambda: query_id(args.nsv_id),
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
