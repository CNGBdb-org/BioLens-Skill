#!/usr/bin/env python3
"""Query UCSC Genome Browser API — track, gene, region, conservation."""

from __future__ import annotations

import argparse
import re
import sys

import requests

API = "https://api.genome.ucsc.edu"
DEFAULT_GENOME = "hg38"
DISPLAY_LIMIT = 5


def parse_region(region: str) -> tuple[str, int, int]:
    m = re.match(r"^(?:chr)?(\w+):(\d+)-(\d+)$", region.strip(), re.I)
    if m:
        chrom = m.group(1)
        if not chrom.startswith("chr"):
            chrom = f"chr{chrom}"
        return chrom, int(m.group(2)), int(m.group(3))
    parts = region.split()
    if len(parts) == 3:
        chrom = parts[0] if parts[0].startswith("chr") else f"chr{parts[0]}"
        return chrom, int(parts[1]), int(parts[2])
    raise ValueError(f"无法解析区域：{region}")


def get_track(genome: str, track: str, chrom: str, start: int, end: int) -> dict:
    r = requests.get(
        f"{API}/getData/track",
        params={"genome": genome, "track": track, "chrom": chrom, "start": start, "end": end},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()


def query_track(track: str, region: str, genome: str) -> None:
    chrom, start, end = parse_region(region)
    print(f"【UCSC 查询】Track：{track}  区域：{chrom}:{start}-{end}  基因组：{genome}")
    data = get_track(genome, track, chrom, start, end)
    items = data.get("knownGene") or data.get("refGene") or data.get(track) or []
    if isinstance(data, dict) and not items:
        for k, v in data.items():
            if isinstance(v, list) and v and k not in ("downloadTime", "genome"):
                items = v
                print(f"  Track 数据键: {k}")
                break
    if not items:
        print(f"  该区间无 {track} 数据（或 track 名称需调整）")
        print(f"  API 响应键: {list(data.keys())}")
        return
    for i, item in enumerate(items[:DISPLAY_LIMIT], 1):
        if isinstance(item, dict):
            name = item.get("name") or item.get("name2") or item.get("geneName") or "N/A"
            print(f"  [{i}] {name}  {item.get('chrom', chrom)}:{item.get('chromStart', item.get('txStart', '?'))}-"
                  f"{item.get('chromEnd', item.get('txEnd', '?'))}")
        else:
            print(f"  [{i}] {item}")
    print(f"\n展示前 {min(DISPLAY_LIMIT, len(items))} 条")


def query_gene(symbol: str, genome: str) -> None:
    """Gene search via /search (param must be ``search=``, not ``query=``)."""
    print(f"【UCSC 查询】基因：{symbol}  基因组：{genome}")
    r = requests.get(
        f"{API}/search",
        params={"genome": genome, "search": symbol},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    # Official shape: { positionMatches: [ { trackName, matches: [ { position, posName, ... } ] } ] }
    groups = data.get("positionMatches") if isinstance(data, dict) else None
    flat: list[tuple[str, dict]] = []
    if isinstance(groups, list):
        for g in groups:
            track = (g.get("trackName") or g.get("name") or "?") if isinstance(g, dict) else "?"
            for m in (g.get("matches") or []) if isinstance(g, dict) else []:
                if isinstance(m, dict):
                    flat.append((track, m))
    if not flat:
        print("  未找到基因，可尝试 region + knownGene track")
        if isinstance(data, dict) and data.get("error"):
            print(f"  API error: {data.get('error')}")
        return

    def _rank(pair: tuple[str, dict]) -> tuple:
        track, item = pair
        name = item.get("posName") or item.get("hgFindMatches") or ""
        # Exact gene hit: "BRCA1 (...)" / "BRCA1" — not "BRCA1 associated ..."
        exact = 0 if re.match(rf"^{re.escape(symbol)}\s*(\(|$)", name, re.I) else 1
        prefer = ("mane", "knownGene", "ncbiRefSeq", "refGene", "wgEncodeGencode", "geneSymbol")
        tscore = next((i for i, p in enumerate(prefer) if p.lower() in track.lower()), 99)
        return (exact, tscore, track)

    flat.sort(key=_rank)
    shown = [p for p in flat if _rank(p)[0] == 0] or flat
    for i, (track, item) in enumerate(shown[:DISPLAY_LIMIT], 1):
        pos = item.get("position") or "N/A"
        name = item.get("posName") or item.get("hgFindMatches") or "N/A"
        name = name.replace("&#x2F;", "/").replace("&amp;", "&")
        desc = (item.get("description") or "")[:80]
        print(f"  [{i}] [{track}] {name}")
        print(f"      位置: {pos}" + (f"  {desc}" if desc else ""))
    print(f"\n精确/优先匹配 {len(shown)} 条（全文检索共 {len(flat)}），展示前 {min(DISPLAY_LIMIT, len(shown))} 条")


def query_region(region: str, genome: str) -> None:
    chrom, start, end = parse_region(region)
    print(f"【UCSC 查询】区域：{chrom}:{start}-{end}")
    query_track("knownGene", region, genome)


def query_conservation(region: str, genome: str) -> None:
    chrom, start, end = parse_region(region)
    print(f"【UCSC 查询】保守性：{chrom}:{start}-{end}")
    for track in ("phastCons100way", "phastCons30way"):
        try:
            data = get_track(genome, track, chrom, start, end)
            scores = data.get(track) or data.get("values") or []
            if scores:
                print(f"  {track}: 有数据（{len(scores) if isinstance(scores, list) else 'ok'}）")
                return
        except requests.RequestException:
            continue
    print("  保守性 track 在该区间无直接数值，建议使用 phastCons bigWig 或 Ensembl 保守性分数")


def main() -> None:
    parser = argparse.ArgumentParser(description="Query UCSC Genome Browser API")
    parser.add_argument("--genome", default=DEFAULT_GENOME, help="Genome assembly (default hg38)")
    sub = parser.add_subparsers(dest="mode", required=True)
    p = sub.add_parser("track", help="Query a UCSC track in region")
    p.add_argument("track")
    p.add_argument("region")
    sub.add_parser("gene", help="Search gene").add_argument("symbol")
    sub.add_parser("region", help="Genes in region (knownGene)").add_argument("region")
    sub.add_parser("conservation", help="Conservation scores in region").add_argument("region")
    args = parser.parse_args()
    handlers = {
        "track": lambda: query_track(args.track, args.region, args.genome),
        "gene": lambda: query_gene(args.symbol, args.genome),
        "region": lambda: query_region(args.region, args.genome),
        "conservation": lambda: query_conservation(args.region, args.genome),
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
