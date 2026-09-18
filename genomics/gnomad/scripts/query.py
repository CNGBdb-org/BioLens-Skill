#!/usr/bin/env python3
"""Query gnomAD: FAF95/grpmax fields + dataset flag + unified JSON."""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import requests

_LIB = Path(__file__).resolve().parent / "_lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from ncbi_http import variation_get  # noqa: E402
from result import emit_json, envelope  # noqa: E402

GNOMAD_API = "https://gnomad.broadinstitute.org/api"
DEFAULT_DATASET = "gnomad_r4"
MIN_REQUEST_INTERVAL = 6.5
MAX_BATCH = 5
DISPLAY_LIMIT = 5
DATASETS = ("gnomad_r4", "gnomad_r3", "gnomad_r2_1")

LOF_CONSEQUENCES = {
    "stop_gained",
    "frameshift_variant",
    "splice_acceptor_variant",
    "splice_donor_variant",
    "start_lost",
    "transcript_ablation",
    "exon_loss_variant",
}

_last_request_at = 0.0

VARIANT_CORE = """
  variant_id
  rsids
  chrom
  pos
  ref
  alt
  exome {
    ac
    an
    ac_hom
    af
    populations { id ac an }
    faf95 {
      popmax
      popmax_population
    }
  }
  genome {
    ac
    an
    ac_hom
    af
    populations { id ac an }
    faf95 {
      popmax
      popmax_population
    }
  }
"""

VARIANT_DETAIL_FIELDS = (
    VARIANT_CORE
    + """
  sortedTranscriptConsequences {
    gene_symbol
    major_consequence
    hgvsc
    hgvsp
  }
"""
)

VARIANT_LIST_FIELDS = (
    VARIANT_CORE
    + """
  transcript_consequence {
    gene_symbol
    major_consequence
  }
"""
)

QUERY_BY_RSID = f"""
query VariantByRsid($rsid: String!, $dataset: DatasetId!) {{
  variant(rsid: $rsid, dataset: $dataset) {{
    {VARIANT_DETAIL_FIELDS}
  }}
}}
"""

QUERY_BY_VARIANT_ID = f"""
query VariantById($variantId: String!, $dataset: DatasetId!) {{
  variant(variantId: $variantId, dataset: $dataset) {{
    {VARIANT_DETAIL_FIELDS}
  }}
}}
"""

QUERY_GENE = """
query GeneConstraint($gene_symbol: String!, $reference_genome: ReferenceGenomeId!) {
  gene(gene_symbol: $gene_symbol, reference_genome: $reference_genome) {
    gene_id
    symbol
    chrom
    start
    stop
    strand
    canonical_transcript_id
    gnomad_constraint {
      exp_lof
      obs_lof
      oe_lof
      oe_lof_upper
      pLI
      lof_z
      mis_z
      syn_z
      oe_mis
      oe_mis_upper
    }
  }
}
"""

QUERY_GENE_VARIANTS = f"""
query GeneVariants($gene_symbol: String!, $reference_genome: ReferenceGenomeId!, $dataset: DatasetId!) {{
  gene(gene_symbol: $gene_symbol, reference_genome: $reference_genome) {{
    symbol
    variants(dataset: $dataset) {{
      {VARIANT_LIST_FIELDS}
    }}
  }}
}}
"""

QUERY_REGION = f"""
query RegionVariants($chrom: String!, $start: Int!, $stop: Int!, $reference_genome: ReferenceGenomeId!, $dataset: DatasetId!) {{
  region(chrom: $chrom, start: $start, stop: $stop, reference_genome: $reference_genome) {{
    variants(dataset: $dataset) {{
      {VARIANT_LIST_FIELDS}
    }}
  }}
}}
"""


def _throttle() -> None:
    global _last_request_at
    elapsed = time.time() - _last_request_at
    if elapsed < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - elapsed)
    _last_request_at = time.time()


def graphql(query: str, variables: dict | None = None, retries: int = 2) -> dict:
    for attempt in range(retries + 1):
        _throttle()
        r = requests.post(
            GNOMAD_API,
            json={"query": query, "variables": variables or {}},
            timeout=120,
        )
        if r.status_code == 429:
            if attempt < retries:
                time.sleep(65)
                continue
            r.raise_for_status()
        if not r.content:
            raise RuntimeError("gnomAD API 返回空响应")
        payload = r.json()
        if r.status_code != 200 or "errors" in payload:
            msgs = "; ".join(e.get("message", str(e)) for e in payload.get("errors", []))
            if msgs:
                raise RuntimeError(msgs)
            r.raise_for_status()
        return payload.get("data", {})
    return {}


def normalize_rsid(rsid: str) -> str:
    rsid = rsid.strip().lower()
    return rsid if rsid.startswith("rs") else f"rs{rsid}"


def calc_af(ac: int | None, an: int | None, stored_af: float | None = None) -> float | None:
    if stored_af is not None:
        return float(stored_af)
    if ac is None or an is None or an == 0:
        return None
    return ac / an


def format_af(ac: int | None, an: int | None, stored_af: float | None = None) -> str:
    value = calc_af(ac, an, stored_af)
    if value is None:
        return "N/A"
    return f"{value:.6g}"


def interpret_af(af: float | None) -> str:
    if af is None:
        return "absent / 无数据 — 支持 PM2（人群罕见）方向，需结合覆盖度"
    if af == 0:
        return "absent (AC=0) — 人群中未见，支持 PM2"
    if af >= 0.05:
        return "常见 (AF≥5%) — 支持 BA1 良性证据，致病可能性低"
    if af >= 0.01:
        return "较常见 (AF≥1%) — 致病可能性较低，需结合 ClinVar"
    if af >= 0.001:
        return "低频 (0.1%≤AF<1%) — 需结合功能与 ClinVar 判断"
    return "极罕见 (AF<0.1%) — 与致病变异相容，需结合 ClinVar"


def _consequence(variant: dict) -> str:
    tx = (variant.get("sortedTranscriptConsequences") or variant.get("transcript_consequence") or [{}])
    if isinstance(tx, dict):
        tx = [tx]
    if tx:
        return tx[0].get("major_consequence") or "N/A"
    return "N/A"


def _gene_symbol(variant: dict) -> str:
    tx = (variant.get("sortedTranscriptConsequences") or variant.get("transcript_consequence") or [{}])
    if isinstance(tx, dict):
        tx = [tx]
    if tx:
        return tx[0].get("gene_symbol") or "N/A"
    return "N/A"


def best_af(variant: dict) -> float | None:
    for block_name in ("exome", "genome"):
        block = variant.get(block_name) or {}
        af = calc_af(block.get("ac"), block.get("an"), block.get("af"))
        if af is not None:
            return af
    return None


def format_faf(block: dict | None) -> str:
    if not block:
        return "N/A"
    faf = block.get("faf95") or {}
    popmax = faf.get("popmax")
    pop = faf.get("popmax_population")
    if popmax is None:
        return "N/A"
    pop_s = pop or "?"
    return f"{popmax:.6g} (grpmax pop={pop_s})"


def format_freq_block(label: str, block: dict | None) -> None:
    if not block:
        print(f"  {label}: 无数据")
        return
    ac, an = block.get("ac"), block.get("an")
    print(f"  {label} AC/AN: {ac}/{an}")
    print(f"  {label} AF: {format_af(ac, an, block.get('af'))}")
    print(f"  {label} FAF95/grpmax: {format_faf(block)}")
    hom = block.get("ac_hom")
    if hom is not None:
        print(f"  {label} 纯合数: {hom}")
    pops = block.get("populations") or []
    top = sorted(
        (p for p in pops if p.get("an")),
        key=lambda p: (p.get("ac") or 0) / p["an"],
        reverse=True,
    )[:5]
    if top:
        print(f"  {label} 主要人群频率:")
        for p in top:
            print(
                f"    {p['id']}: AF={format_af(p.get('ac'), p.get('an'), p.get('af'))} "
                f"({p.get('ac')}/{p.get('an')})"
            )


def print_variant(variant: dict) -> None:
    rsids = ", ".join(variant.get("rsids") or []) or "N/A"
    print(f"  variant_id: {variant.get('variant_id', 'N/A')}")
    print(f"  rsids: {rsids}")
    print(f"  坐标: {variant.get('chrom')}:{variant.get('pos')} {variant.get('ref')}>{variant.get('alt')}")
    if _gene_symbol(variant) != "N/A" or _consequence(variant) != "N/A":
        print(f"  基因: {_gene_symbol(variant)}")
        print(f"  后果: {_consequence(variant)}")
        tx = (variant.get("sortedTranscriptConsequences") or variant.get("transcript_consequence") or [{}])
        if isinstance(tx, dict):
            tx = [tx]
        if tx and tx[0].get("hgvsc"):
            hgvs = f"{tx[0].get('hgvsc')} {tx[0].get('hgvsp') or ''}".strip()
            print(f"  HGVS: {hgvs}")
    format_freq_block("Exome", variant.get("exome"))
    format_freq_block("Genome", variant.get("genome"))
    print(f"  解读: {interpret_af(best_af(variant))}")


def print_variant_row(variant: dict) -> None:
    rsids = ", ".join(variant.get("rsids") or []) or "-"
    vid = variant.get("variant_id", "N/A")
    coord = f"{variant.get('chrom')}:{variant.get('pos')} {variant.get('ref')}>{variant.get('alt')}"
    af = best_af(variant)
    af_str = f"{af:.6g}" if af is not None else "absent"
    print(
        f"  {rsids:<18} {vid:<22} {coord:<24} {_consequence(variant):<22} AF={af_str}"
    )


def variant_ids_from_ncbi(rsid: str) -> list[str]:
    num = rsid.lower().replace("rs", "")
    data = variation_get(f"refsnp/{num}")
    if not data:
        return []
    ids: list[str] = []
    placements = data.get("primary_snapshot_data", {}).get("placements_with_allele", [])
    for placement in placements:
        annot = placement.get("placement_annot", {})
        traits = annot.get("seq_id_traits_by_assembly") or []
        if not any(t.get("assembly_name", "").startswith("GRCh38") for t in traits):
            continue
        chrom = placement.get("seq_id", "").replace("NC_0000", "").replace("NC_000", "")
        chrom = chrom.split(".")[0].lstrip("0") or "0"
        if chrom.isdigit():
            chrom = str(int(chrom))
        for item in placement.get("alleles", []):
            spdi = (item.get("allele") or {}).get("spdi") or {}
            pos = spdi.get("position")
            ref = spdi.get("deleted_sequence")
            alt = spdi.get("inserted_sequence")
            if pos is None or ref is None or alt is None or ref == alt:
                continue
            ids.append(f"{chrom}-{pos}-{ref}-{alt}")
    return ids


def build_variant_id(chrom: str, pos: str | int, ref: str, alt: str) -> str:
    chrom = chrom.replace("chr", "")
    return f"{chrom}-{pos}-{ref}-{alt}"


def parse_region(region_arg: str) -> tuple[str, int, int]:
    region_arg = region_arg.strip()
    m = re.match(r"^(?:chr)?(\d+|X|Y|MT)[:\s-]+(\d+)[:\s-]+(\d+)$", region_arg, re.I)
    if m:
        chrom, start, end = m.group(1), int(m.group(2)), int(m.group(3))
        if start > end:
            start, end = end, start
        return chrom, start, end
    m = re.match(r"^(\d+|X|Y|MT)\s+(\d+)\s+(\d+)$", region_arg, re.I)
    if m:
        chrom, start, end = m.group(1), int(m.group(2)), int(m.group(3))
        if start > end:
            start, end = end, start
        return chrom, start, end
    raise ValueError(
        f"无法解析区域格式：{region_arg}（示例：chr17:43057060-43057065 或 17 43057060 43057065）"
    )


def query_variant_by_rsid(rsid: str, dataset: str = DEFAULT_DATASET) -> dict | None:
    data = graphql(QUERY_BY_RSID, {"rsid": rsid, "dataset": dataset})
    variant = data.get("variant")
    if variant:
        return variant
    for vid in variant_ids_from_ncbi(rsid):
        data = graphql(QUERY_BY_VARIANT_ID, {"variantId": vid, "dataset": dataset})
        variant = data.get("variant")
        if variant:
            return variant
    return None


def query_variant_by_id(variant_id: str, dataset: str = DEFAULT_DATASET) -> dict | None:
    data = graphql(QUERY_BY_VARIANT_ID, {"variantId": variant_id, "dataset": dataset})
    return data.get("variant")


def query_gene_data(gene: str) -> dict | None:
    data = graphql(QUERY_GENE, {"gene_symbol": gene, "reference_genome": "GRCh38"})
    return data.get("gene")


def fetch_gene_variants(gene: str, dataset: str = DEFAULT_DATASET) -> list[dict]:
    data = graphql(
        QUERY_GENE_VARIANTS,
        {"gene_symbol": gene, "reference_genome": "GRCh38", "dataset": dataset},
    )
    gene_data = data.get("gene") or {}
    return gene_data.get("variants") or []


def fetch_region_variants(chrom: str, start: int, stop: int, dataset: str = DEFAULT_DATASET) -> list[dict]:
    data = graphql(
        QUERY_REGION,
        {
            "chrom": chrom,
            "start": start,
            "stop": stop,
            "reference_genome": "GRCh38",
            "dataset": dataset,
        },
    )
    region_data = data.get("region") or {}
    return region_data.get("variants") or []


def filter_gene_variants(variants: list[dict], mode: str) -> list[dict]:
    filtered: list[dict] = []
    for v in variants:
        af = best_af(v)
        cons = _consequence(v)
        if mode == "rare":
            if af is None or af < 0.01:
                filtered.append(v)
        elif mode == "common":
            if af is not None and af >= 0.01:
                filtered.append(v)
        elif mode == "lof":
            if cons in LOF_CONSEQUENCES:
                filtered.append(v)
        elif mode == "missense":
            if cons == "missense_variant":
                filtered.append(v)
    if mode == "rare":
        filtered.sort(key=lambda v: best_af(v) if best_af(v) is not None else -1)
    elif mode == "common":
        filtered.sort(key=lambda v: best_af(v) or 0, reverse=True)
    return filtered


def run_rsid(rsid: str, dataset: str = DEFAULT_DATASET) -> str:
    rsid = normalize_rsid(rsid)
    print(f"【gnomAD 查询】rsID：{rsid}（dataset: {dataset}）")
    variant = query_variant_by_rsid(rsid, dataset=dataset)
    if not variant:
        print("gnomAD 中未找到该变异（可能 absent / 未收录）")
        return "未找到"
    print_variant(variant)
    return "查询完成"


def run_variant(variant_id: str, dataset: str = DEFAULT_DATASET) -> str:
    print(f"【gnomAD 查询】variant_id：{variant_id}（dataset: {dataset}）")
    variant = query_variant_by_id(variant_id, dataset=dataset)
    if not variant:
        print("gnomAD 中未找到该变异")
        return "未找到"
    print_variant(variant)
    return "查询完成"


def run_coord(chrom: str, pos: str, ref: str, alt: str, dataset: str = DEFAULT_DATASET) -> str:
    variant_id = build_variant_id(chrom, pos, ref, alt)
    print(f"【gnomAD 查询】坐标：chr{chrom}:{pos} {ref}>{alt} → {variant_id}")
    return run_variant(variant_id, dataset=dataset)


def run_gene(gene: str) -> str:
    print(f"【gnomAD 查询】基因约束：{gene}")
    gene_data = query_gene_data(gene)
    if not gene_data:
        print("未找到该基因")
        return "未找到"
    c = gene_data.get("gnomad_constraint") or {}
    symbol = gene_data.get("symbol") or gene
    print(f"  基因: {symbol} ({gene_data.get('gene_id', 'N/A')})")
    print(f"  坐标: {gene_data.get('chrom')}:{gene_data.get('start')}-{gene_data.get('stop')}")
    print(f"  链: {gene_data.get('strand', 'N/A')}")
    pli = c.get("pLI")
    loeuf = c.get("oe_lof_upper")
    print(f"  pLI: {pli if pli is not None else 'N/A'}  (>0.9 = LoF 不耐受)")
    print(f"  LOEUF (oe_lof_upper): {loeuf if loeuf is not None else 'N/A'}  (<0.35 = 高度约束)")
    print(f"  oe_lof: {c.get('oe_lof', 'N/A')}")
    print(f"  oe_mis: {c.get('oe_mis', 'N/A')}  / oe_mis_upper: {c.get('oe_mis_upper', 'N/A')}")
    print(f"  obs_lof / exp_lof: {c.get('obs_lof', 'N/A')} / {c.get('exp_lof', 'N/A')}")
    print(f"  lof_z: {c.get('lof_z', 'N/A')}  / mis_z: {c.get('mis_z', 'N/A')}  / syn_z: {c.get('syn_z', 'N/A')}")
    if pli is not None and pli > 0.9:
        print("  解读: 高 pLI，基因对 LoF 变异不耐受，LoF 更可能致病")
    elif loeuf is not None and loeuf < 0.35:
        print("  解读: 低 LOEUF，基因高度约束")
    else:
        print("  解读: 约束指标未达典型高约束阈值，需结合具体变异判断")
    return "查询完成"


def run_region(region: str, dataset: str = DEFAULT_DATASET) -> str:
    chrom, start, stop = parse_region(region)
    print(f"【gnomAD 查询】区域：chr{chrom}:{start}-{stop}（dataset: {dataset}）")
    variants = fetch_region_variants(chrom, start, stop, dataset=dataset)
    if not variants:
        print("该区域无 gnomAD 变异记录")
        return "未查询到"
    print(f"\n{'rsID':<18} {'variant_id':<22} {'坐标':<24} {'后果':<22} 频率")
    print("-" * 100)
    for v in variants[:DISPLAY_LIMIT]:
        print_variant_row(v)
    print(f"\n共 {len(variants)} 个变异，展示前 {min(DISPLAY_LIMIT, len(variants))} 个")
    return "查询完成"


def run_gene_variants(gene: str, mode: str, dataset: str = DEFAULT_DATASET) -> str:
    labels = {
        "rare": f"基因罕见变异 (AF<1%)：{gene}",
        "common": f"基因常见变异 (AF≥1%)：{gene}",
        "lof": f"基因 LoF 变异：{gene}",
        "missense": f"基因 missense 变异：{gene}",
    }
    print(f"【gnomAD 查询】{labels[mode]}（dataset: {dataset}）")
    print("  正在获取基因变异（CDS ±75bp），请稍候…")
    variants = fetch_gene_variants(gene, dataset=dataset)
    if not variants:
        print("未找到该基因变异")
        return "未查询到"
    filtered = filter_gene_variants(variants, mode)
    print(f"  基因总变异: {len(variants)}，符合筛选: {len(filtered)}")
    if not filtered:
        print("无符合筛选条件的变异")
        return "未查询到"
    print(f"\n{'rsID':<18} {'variant_id':<22} {'坐标':<24} {'后果':<22} 频率")
    print("-" * 100)
    for v in filtered[:DISPLAY_LIMIT]:
        print_variant_row(v)
    print(f"\n展示前 {min(DISPLAY_LIMIT, len(filtered))} 条")
    return "查询完成"


def run_batch(rsids: list[str], dataset: str = DEFAULT_DATASET) -> str:
    if len(rsids) > MAX_BATCH:
        print(f"警告：批量查询最多 {MAX_BATCH} 个 rsID（gnomAD 限流 10 次/分钟），已截断")
        rsids = rsids[:MAX_BATCH]
    print(f"【gnomAD 批量查询】{len(rsids)} 个 rsID（dataset: {dataset}）")
    print(f"{'rsID':<16} {'variant_id':<22} {'AF (exome)':<12} {'解读'}")
    print("-" * 80)
    for rsid in rsids:
        rsid = normalize_rsid(rsid)
        variant = query_variant_by_rsid(rsid, dataset=dataset)
        if not variant:
            print(f"{rsid:<16} {'未找到':<22}")
            continue
        exome = variant.get("exome") or {}
        af = format_af(exome.get("ac"), exome.get("an"), exome.get("af"))
        print(f"{rsid:<16} {variant.get('variant_id', 'N/A'):<22} {af:<12} {interpret_af(best_af(variant))[:30]}")
    return "查询完成"


def variant_to_record(variant: dict) -> dict:
    rsids = ", ".join(variant.get("rsids") or []) or "N/A"
    tx = (variant.get("sortedTranscriptConsequences") or variant.get("transcript_consequence") or [{}])
    if isinstance(tx, dict):
        tx = [tx]
    hgvs = ""
    if tx and tx[0].get("hgvsc"):
        hgvs = f"{tx[0].get('hgvsc')} {tx[0].get('hgvsp') or ''}".strip()
    exome = variant.get("exome") or {}
    genome = variant.get("genome") or {}
    af = best_af(variant)
    pops = []
    for block in (exome, genome):
        for p in (block.get("populations") or [])[:5]:
            pops.append(f"{p.get('id')}={format_af(p.get('ac'), p.get('an'), p.get('af'))}")
    return {
        "rsID": rsids,
        "variant_id": variant.get("variant_id", "N/A"),
        "坐标": f"{variant.get('chrom')}:{variant.get('pos')} {variant.get('ref')}>{variant.get('alt')}",
        "基因": _gene_symbol(variant),
        "后果": _consequence(variant),
        "HGVS": hgvs or "N/A",
        "Exome AF": format_af(exome.get("ac"), exome.get("an"), exome.get("af")),
        "Exome FAF95/grpmax": format_faf(exome),
        "Genome AF": format_af(genome.get("ac"), genome.get("an"), genome.get("af")),
        "Genome FAF95/grpmax": format_faf(genome),
        "主要人群 AF": "; ".join(pops[:5]) if pops else "N/A",
        "解读": interpret_af(af),
    }


def variant_to_row(variant: dict) -> dict:
    af = best_af(variant)
    return {
        "rsID": ", ".join(variant.get("rsids") or []) or "-",
        "variant_id": variant.get("variant_id", "N/A"),
        "坐标": f"{variant.get('chrom')}:{variant.get('pos')} {variant.get('ref')}>{variant.get('alt')}",
        "后果": _consequence(variant),
        "AF": f"{af:.6g}" if af is not None else "absent",
    }


def build_rsid_json(rsid: str, dataset: str = DEFAULT_DATASET) -> dict:
    rsid = normalize_rsid(rsid)
    variant = query_variant_by_rsid(rsid, dataset=dataset)
    if not variant:
        return envelope(
            source="gnomad", mode="rsid", ok=False, label=rsid, message="variant not found in gnomAD"
        )
    rec = variant_detail_payload(variant)
    return envelope(
        source="gnomad",
        mode="rsid",
        label=rsid,
        total=1,
        returned=1,
        record=rec,
        extra={"dataset": dataset, "interpretation": rec.get("interpretation")},
    )


def build_gene_constraint_json(gene: str) -> dict:
    gene_data = query_gene_data(gene)
    if not gene_data:
        return envelope(source="gnomad", mode="gene", ok=False, label=gene, message="未找到该基因")
    c = gene_data.get("gnomad_constraint") or {}
    pli = c.get("pLI")
    loeuf = c.get("oe_lof_upper")
    interp = "需结合具体变异判断"
    if pli is not None and pli > 0.9:
        interp = "高 pLI，基因对 LoF 变异不耐受，LoF 更可能致病"
    elif loeuf is not None and loeuf < 0.35:
        interp = "低 LOEUF，基因高度约束"
    return envelope(
        source="gnomad",
        mode="gene",
        label=gene,
        total=1,
        returned=1,
        record={
            "gene": gene_data.get("symbol") or gene,
            "gene_id": gene_data.get("gene_id"),
            "chrom": gene_data.get("chrom"),
            "start": gene_data.get("start"),
            "stop": gene_data.get("stop"),
            "constraint": {
                "pLI": pli,
                "LOEUF": loeuf,
                "oe_lof": c.get("oe_lof"),
                "oe_mis": c.get("oe_mis"),
                "lof_z": c.get("lof_z"),
                "mis_z": c.get("mis_z"),
            },
            "interpretation": interp,
        },
        extra={"interpretation": interp},
    )


def build_gene_variants_json(gene: str, mode: str, dataset: str = DEFAULT_DATASET) -> dict:
    variants = fetch_gene_variants(gene, dataset=dataset)
    if not variants:
        return envelope(source="gnomad", mode=mode, ok=False, label=gene, message="未找到该基因变异")
    filtered = filter_gene_variants(variants, mode)
    shown = filtered[:DISPLAY_LIMIT]
    return envelope(
        source="gnomad",
        mode=mode,
        label=gene,
        total=len(filtered),
        returned=len(shown),
        records=[variant_to_row(v) for v in shown],
        extra={"dataset": dataset, "gene_total": len(variants)},
    )




def _faf_payload(block: dict | None) -> dict | None:
    if not block:
        return None
    faf = block.get("faf95") or {}
    return {
        "af": calc_af(block.get("ac"), block.get("an"), block.get("af")),
        "ac": block.get("ac"),
        "an": block.get("an"),
        "ac_hom": block.get("ac_hom"),
        "faf95_popmax": faf.get("popmax"),
        "faf95_popmax_population": faf.get("popmax_population"),
    }


def variant_detail_payload(variant: dict) -> dict:
    return {
        "variant_id": variant.get("variant_id"),
        "rsids": variant.get("rsids") or [],
        "chrom": variant.get("chrom"),
        "pos": variant.get("pos"),
        "ref": variant.get("ref"),
        "alt": variant.get("alt"),
        "gene": _gene_symbol(variant),
        "consequence": _consequence(variant),
        "exome": _faf_payload(variant.get("exome")),
        "genome": _faf_payload(variant.get("genome")),
        "interpretation": interpret_af(best_af(variant)),
    }


def _variant_json(variant_id: str, dataset: str) -> dict:
    variant = query_variant_by_id(variant_id, dataset=dataset)
    if not variant:
        return envelope(source="gnomad", mode="variant", ok=False, label=variant_id, message="not found")
    return envelope(
        source="gnomad",
        mode="variant",
        label=variant_id,
        total=1,
        returned=1,
        record=variant_detail_payload(variant),
        extra={"dataset": dataset},
    )


def _coord_json(chrom: str, pos: str, ref: str, alt: str, dataset: str) -> dict:
    vid = build_variant_id(chrom, pos, ref, alt)
    return _variant_json(vid, dataset)


def _region_json(region: str, dataset: str) -> dict:
    chrom, start, stop = parse_region(region)
    variants = fetch_region_variants(chrom, start, stop, dataset=dataset)
    return envelope(
        source="gnomad",
        mode="region",
        label=region,
        total=len(variants),
        returned=min(DISPLAY_LIMIT, len(variants)),
        records=[variant_to_row(v) for v in variants[:DISPLAY_LIMIT]],
        extra={"dataset": dataset},
    )


def _batch_json(rsids: list[str], dataset: str) -> dict:
    if len(rsids) > MAX_BATCH:
        return envelope(source="gnomad", mode="batch", ok=False, message=f"max {MAX_BATCH} rsIDs")
    rows = []
    for rsid in rsids:
        v = query_variant_by_rsid(normalize_rsid(rsid), dataset=dataset)
        rows.append({"rsid": rsid, "found": bool(v), "record": variant_detail_payload(v) if v else None})
    return envelope(
        source="gnomad",
        mode="batch",
        total=len(rsids),
        returned=len(rows),
        records=rows,
        extra={"dataset": dataset},
    )



def main() -> None:
    parser = argparse.ArgumentParser(description="Query gnomAD variant frequency or gene constraint")
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--format", choices=["text", "json"], default="text")
    parent.add_argument("--dataset", choices=DATASETS, default=DEFAULT_DATASET)
    sub = parser.add_subparsers(dest="mode", required=True)

    rsid_p = sub.add_parser("rsid", parents=[parent], help="Query allele frequency by rsID")
    rsid_p.add_argument("rsid", help="rsID, e.g. rs80357906")

    var_p = sub.add_parser("variant", parents=[parent], help="Query by gnomAD variant ID (CHROM-POS-REF-ALT)")
    var_p.add_argument("variant_id", help="e.g. 17-43057062-T-TG")

    coord_p = sub.add_parser("coord", parents=[parent], help="Query by chrom/pos/ref/alt")
    coord_p.add_argument("chrom", help="Chromosome, e.g. 17")
    coord_p.add_argument("pos", help="Position")
    coord_p.add_argument("ref", help="Reference allele")
    coord_p.add_argument("alt", help="Alternate allele")

    gene_p = sub.add_parser("gene", parents=[parent], help="Query gene constraint scores (pLI, LOEUF)")
    gene_p.add_argument("gene", help="Gene symbol, e.g. BRCA1")

    region_p = sub.add_parser("region", parents=[parent], help="Variants in a genomic region")
    region_p.add_argument("region", help="chr17:43057060-43057065 or '17 43057060 43057065'")

    for name, help_text in [
        ("rare", "Rare gene variants (AF < 1%%)"),
        ("common", "Common gene variants (AF >= 1%%)"),
        ("lof", "Predicted loss-of-function variants in gene"),
        ("missense", "Missense variants in gene"),
    ]:
        p = sub.add_parser(name, parents=[parent], help=help_text)
        p.add_argument("gene", help="Gene symbol")

    batch_p = sub.add_parser("batch", parents=[parent], help=f"Batch rsID lookup (max {MAX_BATCH})")
    batch_p.add_argument("rsids", nargs="+", help="rsIDs to query")

    args = parser.parse_args()

    json_handlers = {
        "rsid": lambda: build_rsid_json(args.rsid, dataset=args.dataset),
        "variant": lambda: _variant_json(args.variant_id, args.dataset),
        "coord": lambda: _coord_json(args.chrom, args.pos, args.ref, args.alt, args.dataset),
        "gene": lambda: build_gene_constraint_json(args.gene),
        "region": lambda: _region_json(args.region, args.dataset),
        "rare": lambda: build_gene_variants_json(args.gene, "rare", dataset=args.dataset),
        "common": lambda: build_gene_variants_json(args.gene, "common", dataset=args.dataset),
        "lof": lambda: build_gene_variants_json(args.gene, "lof", dataset=args.dataset),
        "missense": lambda: build_gene_variants_json(args.gene, "missense", dataset=args.dataset),
        "batch": lambda: _batch_json(args.rsids, args.dataset),
    }

    if args.format == "json" and args.mode in json_handlers:
        try:
            emit_json(json_handlers[args.mode]())
        except ValueError as exc:
            emit_json(envelope(source="gnomad", mode=args.mode, ok=False, message=str(exc)))
            sys.exit(1)
        except (requests.RequestException, RuntimeError) as exc:
            emit_json(envelope(source="gnomad", mode=args.mode, ok=False, message=f"查询失败：{exc}"))
            sys.exit(1)
        return

    handlers = {
        "rsid": lambda: run_rsid(args.rsid, dataset=args.dataset),
        "variant": lambda: run_variant(args.variant_id, dataset=args.dataset),
        "coord": lambda: run_coord(args.chrom, args.pos, args.ref, args.alt, dataset=args.dataset),
        "gene": lambda: run_gene(args.gene),
        "region": lambda: run_region(args.region, dataset=args.dataset),
        "rare": lambda: run_gene_variants(args.gene, "rare", dataset=args.dataset),
        "common": lambda: run_gene_variants(args.gene, "common", dataset=args.dataset),
        "lof": lambda: run_gene_variants(args.gene, "lof", dataset=args.dataset),
        "missense": lambda: run_gene_variants(args.gene, "missense", dataset=args.dataset),
        "batch": lambda: run_batch(args.rsids, dataset=args.dataset),
    }
    try:
        handlers[args.mode]()
    except ValueError as exc:
        print(f"错误：{exc}", file=sys.stderr)
        sys.exit(1)
    except (requests.RequestException, RuntimeError) as exc:
        print(f"查询失败：{exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
