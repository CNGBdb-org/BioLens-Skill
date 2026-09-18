#!/usr/bin/env python3
"""Query Ensembl REST API — gene, variant, region, homology, VEP."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import requests

_LIB = Path(__file__).resolve().parent / "_lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from result import emit_json, envelope  # noqa: E402

BASE = "https://rest.ensembl.org"
SPECIES = "homo_sapiens"
DISPLAY_LIMIT = 5


def api_get(path: str, params: dict | None = None) -> dict | list:
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    r = requests.get(url, params=params, headers=headers, timeout=60)
    r.raise_for_status()
    if not r.content:
        return {}
    return r.json()


def api_post(path: str, payload: dict | list) -> dict | list:
    url = f"{BASE}{path}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    r = requests.post(url, json=payload, headers=headers, timeout=120)
    r.raise_for_status()
    return r.json() if r.content else {}


def parse_region(region: str) -> tuple[str, int, int]:
    m = re.match(r"^(?:chr)?(\w+):(\d+)-(\d+)$", region.strip(), re.I)
    if m:
        return m.group(1), int(m.group(2)), int(m.group(3))
    parts = region.split()
    if len(parts) == 3:
        return parts[0].replace("chr", ""), int(parts[1]), int(parts[2])
    raise ValueError(f"无法解析区域：{region}（示例 chr17:43044295-43170245）")


def _gene_record(data: dict) -> dict:
    children = data.get("Transcript") or data.get("transcript") or []
    if isinstance(children, dict):
        children = list(children.values())
    return {
        "ensembl_id": data.get("id", "N/A"),
        "name": data.get("display_name", "N/A"),
        "description": data.get("description", "N/A"),
        "biotype": data.get("biotype", "N/A"),
        "coord": (
            f"chr{data.get('seq_region_name')}:{data.get('start')}-{data.get('end')} "
            f"({data.get('assembly_name', 'GRCh38')})"
        ),
        "strand": "+" if data.get("strand") == 1 else "-",
        "transcripts": [
            {
                "id": tx.get("id"),
                "biotype": tx.get("biotype"),
                "start": tx.get("start"),
                "end": tx.get("end"),
            }
            for tx in children[:DISPLAY_LIMIT]
        ],
    }


def query_gene(symbol: str) -> None:
    print(f"【Ensembl 查询】基因：{symbol}")
    data = api_get(f"/lookup/symbol/{SPECIES}/{symbol}", {"expand": 1})
    rec = _gene_record(data)
    print(f"  Ensembl ID: {rec['ensembl_id']}")
    print(f"  名称: {rec['name']}")
    print(f"  描述: {rec['description']}")
    print(f"  类型: {rec['biotype']}")
    print(f"  坐标: {rec['coord']}")
    print(f"  链: {rec['strand']}")
    if rec["transcripts"]:
        print(f"\n  转录本（前 {DISPLAY_LIMIT} 个）:")
        for tx in rec["transcripts"]:
            print(f"    {tx.get('id')}  {tx.get('biotype')}  {tx.get('start')}-{tx.get('end')}")


def query_variant(variant_id: str) -> None:
    print(f"【Ensembl 查询】变异：{variant_id}")
    data = api_get(f"/variation/{SPECIES}/{variant_id}")
    print(f"  名称: {data.get('name', 'N/A')}")
    print(f"  等位基因: {', '.join(data.get('alleles', []))}")
    mappings = data.get("mappings") or []
    for m in mappings[:3]:
        print(f"  坐标: chr{m.get('seq_region_name')}:{m.get('start')} ({m.get('assembly_name')})")
    pops = data.get("populations") or []
    if pops:
        print(f"  人群频率（前 {min(3, len(pops))} 条）:")
        for p in pops[:3]:
            print(f"    {p.get('population')}: {p.get('frequency')}")


def query_region(region: str) -> None:
    chrom, start, end = parse_region(region)
    print(f"【Ensembl 查询】区域：chr{chrom}:{start}-{end}")
    data = api_get(f"/overlap/region/{SPECIES}/{chrom}:{start}-{end}", {"feature": "gene"})
    genes = data if isinstance(data, list) else []
    if not genes:
        print("  未找到基因")
        return
    print(f"  共 {len(genes)} 个特征，展示前 {DISPLAY_LIMIT} 个:")
    for g in genes[:DISPLAY_LIMIT]:
        print(
            f"    {g.get('id')}  {g.get('external_name', g.get('display_name', ''))}  "
            f"{g.get('biotype')}  chr{g.get('seq_region_name')}:{g.get('start')}-{g.get('end')}"
        )


def query_homology(symbol: str) -> None:
    print(f"【Ensembl 查询】同源基因：{symbol}")
    gene = api_get(f"/lookup/symbol/{SPECIES}/{symbol}")
    gid = gene.get("id")
    if not gid:
        print("  未找到基因")
        return
    data = api_get(f"/homology/id/{SPECIES}/{gid}", {"type": "orthologues"})
    homologies = (data.get("data") or [{}])[0].get("homologies") or []
    if not homologies:
        print("  未找到同源基因")
        return
    print(f"  展示前 {DISPLAY_LIMIT} 个直系同源:")
    shown = 0
    for h in homologies:
        target = h.get("target") or {}
        species = target.get("species") or "N/A"
        if species == SPECIES:
            continue
        print(
            f"    {target.get('id')}  {target.get('display_id')}  ({species})  "
            f"identity={h.get('target_perc_id')}%"
        )
        shown += 1
        if shown >= DISPLAY_LIMIT:
            break


def query_vep(hgvs: str) -> None:
    print(f"【Ensembl VEP】HGVS：{hgvs}")
    payload = {"hgvs_notations": [hgvs]}
    data = api_post(f"/vep/{SPECIES}/hgvs", payload)
    if not data:
        print("  未返回结果")
        return
    for item in data[:DISPLAY_LIMIT]:
        inp = item.get("input") or hgvs
        print(f"\n  输入: {inp}")
        for tc in (item.get("transcript_consequences") or [])[:3]:
            print(f"    基因: {tc.get('gene_symbol')}  后果: {tc.get('consequence_terms')}")
            print(
                f"    转录本: {tc.get('transcript_id')}  HGVS: {tc.get('hgvsc')} {tc.get('hgvsp') or ''}"
            )
            print(
                f"    影响: {tc.get('impact')}  SIFT: {tc.get('sift_prediction')}  "
                f"PolyPhen: {tc.get('polyphen_prediction')}"
            )


def build_gene_json(symbol: str) -> dict:
    data = api_get(f"/lookup/symbol/{SPECIES}/{symbol}", {"expand": 1})
    if not data or not data.get("id"):
        return envelope(source="ensembl", mode="gene", ok=False, label=symbol, message="未找到基因")
    return envelope(
        source="ensembl", mode="gene", label=symbol, total=1, returned=1, record=_gene_record(data)
    )


def build_variant_json(variant_id: str) -> dict:
    data = api_get(f"/variation/{SPECIES}/{variant_id}")
    if not data or not data.get("name"):
        return envelope(
            source="ensembl", mode="variant", ok=False, label=variant_id, message="未找到变异"
        )
    mappings = [
        {
            "chr": m.get("seq_region_name"),
            "start": m.get("start"),
            "end": m.get("end"),
            "assembly": m.get("assembly_name"),
        }
        for m in (data.get("mappings") or [])[:5]
    ]
    pops = [
        {"population": p.get("population"), "frequency": p.get("frequency")}
        for p in (data.get("populations") or [])[:5]
    ]
    return envelope(
        source="ensembl",
        mode="variant",
        label=variant_id,
        total=1,
        returned=1,
        record={
            "name": data.get("name"),
            "alleles": data.get("alleles") or [],
            "mappings": mappings,
            "populations": pops,
        },
    )


def build_region_json(region: str) -> dict:
    chrom, start, end = parse_region(region)
    data = api_get(f"/overlap/region/{SPECIES}/{chrom}:{start}-{end}", {"feature": "gene"})
    genes = data if isinstance(data, list) else []
    records = [
        {
            "id": g.get("id"),
            "name": g.get("external_name") or g.get("display_name"),
            "biotype": g.get("biotype"),
            "coord": f"chr{g.get('seq_region_name')}:{g.get('start')}-{g.get('end')}",
        }
        for g in genes[:DISPLAY_LIMIT]
    ]
    return envelope(
        source="ensembl",
        mode="region",
        label=region,
        total=len(genes),
        returned=len(records),
        records=records,
    )


def build_homology_json(symbol: str) -> dict:
    gene = api_get(f"/lookup/symbol/{SPECIES}/{symbol}")
    gid = gene.get("id")
    if not gid:
        return envelope(source="ensembl", mode="homology", ok=False, label=symbol, message="未找到基因")
    data = api_get(f"/homology/id/{SPECIES}/{gid}", {"type": "orthologues"})
    homologies = (data.get("data") or [{}])[0].get("homologies") or []
    records = []
    for h in homologies:
        target = h.get("target") or {}
        species = target.get("species") or "N/A"
        if species == SPECIES:
            continue
        records.append(
            {
                "id": target.get("id"),
                "display_id": target.get("display_id"),
                "species": species,
                "identity": h.get("target_perc_id"),
            }
        )
        if len(records) >= DISPLAY_LIMIT:
            break
    return envelope(
        source="ensembl",
        mode="homology",
        label=symbol,
        total=len(records),
        returned=len(records),
        records=records,
    )


def build_vep_json(hgvs: str) -> dict:
    data = api_post(f"/vep/{SPECIES}/hgvs", {"hgvs_notations": [hgvs]})
    if not data:
        return envelope(source="ensembl", mode="vep", ok=False, label=hgvs, message="未返回结果")
    records = []
    for item in data[:DISPLAY_LIMIT]:
        consequences = []
        for tc in (item.get("transcript_consequences") or [])[:5]:
            consequences.append(
                {
                    "gene": tc.get("gene_symbol"),
                    "transcript_id": tc.get("transcript_id"),
                    "consequence_terms": tc.get("consequence_terms"),
                    "hgvsc": tc.get("hgvsc"),
                    "hgvsp": tc.get("hgvsp"),
                    "impact": tc.get("impact"),
                    "sift": tc.get("sift_prediction"),
                    "polyphen": tc.get("polyphen_prediction"),
                }
            )
        records.append({"input": item.get("input") or hgvs, "consequences": consequences})
    return envelope(
        source="ensembl",
        mode="vep",
        label=hgvs,
        total=len(data) if isinstance(data, list) else len(records),
        returned=len(records),
        records=records,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Query Ensembl REST API")
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--format", choices=["text", "json"], default="text")
    sub = parser.add_subparsers(dest="mode", required=True)

    sub.add_parser("gene", parents=[parent], help="Gene lookup by symbol").add_argument("gene")
    sub.add_parser("variant", parents=[parent], help="Variant by rsID or COSMIC ID").add_argument(
        "variant_id"
    )
    sub.add_parser("region", parents=[parent], help="Genes in region").add_argument("region")
    sub.add_parser("homology", parents=[parent], help="Orthologues").add_argument("gene")
    sub.add_parser("vep", parents=[parent], help="VEP by HGVS").add_argument("hgvs")

    args = parser.parse_args()
    json_handlers = {
        "gene": lambda: build_gene_json(args.gene),
        "variant": lambda: build_variant_json(args.variant_id),
        "region": lambda: build_region_json(args.region),
        "homology": lambda: build_homology_json(args.gene),
        "vep": lambda: build_vep_json(args.hgvs),
    }
    if args.format == "json":
        try:
            emit_json(json_handlers[args.mode]())
        except ValueError as exc:
            emit_json(envelope(source="ensembl", mode=args.mode, ok=False, message=str(exc)))
            sys.exit(1)
        except requests.RequestException as exc:
            emit_json(
                envelope(source="ensembl", mode=args.mode, ok=False, message=f"API request failed: {exc}")
            )
            sys.exit(1)
        return

    handlers = {
        "gene": lambda: query_gene(args.gene),
        "variant": lambda: query_variant(args.variant_id),
        "region": lambda: query_region(args.region),
        "homology": lambda: query_homology(args.gene),
        "vep": lambda: query_vep(args.hgvs),
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
