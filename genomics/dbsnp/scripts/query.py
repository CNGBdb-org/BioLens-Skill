#!/usr/bin/env python3
"""Query dbSNP: HGVS resolve + NCBI retry + unified JSON envelope."""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.parse
from pathlib import Path

import requests

_LIB = Path(__file__).resolve().parent / "_lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from ncbi_http import eutils_get, request_delay, variation_get  # noqa: E402
from result import emit_json, envelope  # noqa: E402

DEFAULT_RETMAX = 20
DISPLAY_LIMIT = 5

SNP_CLASS_QUERIES = {
    "SNV": "snv[SNPCLASS]",
    "INS": "ins[SNPCLASS]",
    "DEL": "del[SNPCLASS]",
    "DELINS": "delins[SNPCLASS]",
    "MNV": "mnv[SNPCLASS]",
}


def esearch_snp(term: str, retmax: int = DEFAULT_RETMAX) -> tuple[list[str], str]:
    result = eutils_get(
        "esearch.fcgi",
        {"db": "snp", "term": term, "retmode": "json", "retmax": retmax},
    ).get("esearchresult", {})
    return result.get("idlist", []), result.get("count", "0")


def esummary_snp(ids: list[str]) -> list[dict]:
    if not ids:
        return []
    result = eutils_get(
        "esummary.fcgi",
        {"db": "snp", "id": ",".join(ids), "retmode": "json"},
    ).get("result", {})
    uids = result.get("uids", [])
    return [result[uid] for uid in uids if uid in result]


def normalize_rsid(rsid: str) -> str:
    rsid = rsid.strip().replace("RS", "rs").replace("Rs", "rs")
    if not rsid.lower().startswith("rs"):
        rsid = f"rs{rsid.lstrip('rs')}"
    return rsid


def rsid_number(rsid: str) -> str:
    return normalize_rsid(rsid).lower().replace("rs", "")


def _gene_names(rec: dict) -> str:
    genes = rec.get("genes") or []
    if genes:
        return ", ".join(g.get("name", "") for g in genes if g.get("name"))
    return str(rec.get("gene", "N/A"))


def _parse_spdi(spdi: str) -> tuple[str, str, str]:
    # NC_000017.11:43057062:GGG:GGGG
    parts = (spdi or "").split(":")
    if len(parts) >= 4:
        return parts[1], parts[2], parts[3]
    return "N/A", "N/A", "N/A"


def _format_mafs(rec: dict) -> str:
    mafs = rec.get("global_mafs") or []
    if not mafs:
        legacy = rec.get("global_maf", rec.get("maf"))
        return str(legacy) if legacy not in (None, "", "N/A") else "N/A"
    parts: list[str] = []
    for item in mafs[:6]:
        study = item.get("study", "?")
        freq = item.get("freq", "?")
        parts.append(f"{study}={freq}")
    if len(mafs) > 6:
        parts.append(f"...共 {len(mafs)} 个来源")
    return "; ".join(parts)


def format_snp_record(rec: dict, *, detail: bool = False) -> dict[str, str]:
    rsid = rec.get("snp_id", rec.get("uid", "N/A"))
    if rsid and not str(rsid).startswith("rs"):
        rsid = f"rs{rsid}"
    pos, ref, alt = _parse_spdi(rec.get("spdi", ""))
    info = {
        "rsID": str(rsid),
        "染色体": str(rec.get("chr", "N/A")),
        "位置(GRCh38)": str(rec.get("chrpos", rec.get("position", pos))),
        "等位基因": f"{ref}>{alt}" if ref != "N/A" else str(rec.get("allele", "N/A")),
        "基因": _gene_names(rec),
        "变异类型": str(rec.get("snp_class", "N/A")),
        "功能类型": str(rec.get("fxn_class", rec.get("functional_class", "N/A"))),
        "MAF/频率": _format_mafs(rec),
    }
    if detail:
        info.update(
            {
                "位置(GRCh37)": str(rec.get("chrpos_prev_assm", "N/A")),
                "SPDI": str(rec.get("spdi", "N/A")),
                "验证状态": str(rec.get("validated", "N/A")),
                "临床意义": str(rec.get("clinical_significance", "N/A")),
                "提交来源": str(rec.get("handle", "N/A"))[:120],
            }
        )
    else:
        clinical = rec.get("clinical_significance")
        if clinical not in (None, "", "N/A", "unknown"):
            info["临床意义"] = str(clinical)
    return info


def _format_coord(rec: dict) -> str:
    chrpos = str(rec.get("chrpos", rec.get("position", "")))
    if ":" in chrpos:
        chrom, pos = chrpos.split(":", 1)
        return f"chr{chrom}:{pos}"
    chrom = rec.get("chr", "?")
    return f"chr{chrom}:{chrpos}"


def print_records(records: list[dict], *, detail: bool = False) -> None:
    for i, rec in enumerate(records, 1):
        info = format_snp_record(rec, detail=detail)
        print(f"\n===== 结果 {i} =====")
        for k, v in info.items():
            print(f"  {k}: {v}")


def print_summary(total: str | int, shown: int) -> None:
    total_n = int(total) if str(total).isdigit() else shown
    print(f"\n共检索到 {total_n} 条，展示前 {shown} 条")


def pick_rsid_record(records: list[dict], rsid: str) -> list[dict]:
    target = rsid_number(rsid)
    matched = [r for r in records if str(r.get("snp_id", "")) == target]
    return matched or records


def parse_region(region_arg: str, *, assembly: str = "GRCh38") -> str:
    region_arg = region_arg.strip()
    m = re.match(r"^(?:chr)?(\d+|X|Y|MT)[:\s-]+(\d+)(?:[:\s-]+(\d+))?$", region_arg, re.I)
    if m:
        chrom, start, end = m.group(1), m.group(2), m.group(3) or m.group(2)
        if int(start) > int(end):
            start, end = end, start
        pos_field = "POSITION" if assembly.upper() == "GRCH38" else "POSITION_GRCH37"
        return f"{chrom}[CHR] AND {start}:{end}[{pos_field}]"
    m = re.match(r"^(\d+|X|Y|MT)\s+(\d+)\s+(\d+)$", region_arg, re.I)
    if m:
        chrom, start, end = m.group(1), m.group(2), m.group(3)
        if int(start) > int(end):
            start, end = end, start
        pos_field = "POSITION" if assembly.upper() == "GRCH38" else "POSITION_GRCH37"
        return f"{chrom}[CHR] AND {start}:{end}[{pos_field}]"
    raise ValueError(
        f"无法解析区域格式：{region_arg}（示例：chr17:43057060-43057065 或 17 43057060 43057065）"
    )



def resolve_hgvs_to_rsids(hgvs: str) -> list[str]:
    """Map HGVS -> rsIDs via NCBI Variation Services, fallback to esearch."""
    hgvs = hgvs.strip()
    encoded = urllib.parse.quote(hgvs, safe="")
    data = variation_get(f"hgvs/{encoded}/rsids")
    rsids: list[str] = []
    if isinstance(data, dict):
        for key in ("rsids", "rsid", "data"):
            val = data.get(key)
            if isinstance(val, list):
                rsids.extend(str(x) for x in val)
            elif isinstance(val, (str, int)):
                rsids.append(str(val))
        # nested common shapes
        for item in data.get("rsids") or []:
            if isinstance(item, dict) and item.get("id"):
                rsids.append(str(item["id"]))
    # fallback esearch
    if not rsids:
        term = f'"{hgvs}"[All Fields]'
        ids, _ = esearch_snp(term, retmax=20)
        rsids.extend(ids)
    out = []
    for r in rsids:
        r = str(r)
        if not r.lower().startswith("rs"):
            r = f"rs{r}"
        if r not in out:
            out.append(r)
    return out


def query_by_hgvs(hgvs: str) -> str:
    print(f"【dbSNP 查询】HGVS resolve：{hgvs}")
    rsids = resolve_hgvs_to_rsids(hgvs)
    if not rsids:
        print("未解析到 rsID（可检查 HGVS 是否含转录本/基因组前缀）")
        return "未查询到"
    print(f"  解析到 {len(rsids)} 个 rsID：{', '.join(rsids[:10])}")
    # show first few summaries
    nums = [rsid_number(r) for r in rsids[:DISPLAY_LIMIT]]
    time.sleep(request_delay())
    records = esummary_snp(nums)
    print_records(records, detail=True)
    print(f"\n共解析 {len(rsids)} 个 rsID，展示 {len(records)} 条")
    return "查询完成"


def build_hgvs_json(hgvs: str) -> dict:
    rsids = resolve_hgvs_to_rsids(hgvs)
    if not rsids:
        return envelope(source="dbsnp", mode="hgvs", ok=False, label=hgvs, message="未解析到 rsID")
    nums = [rsid_number(r) for r in rsids[:DISPLAY_LIMIT]]
    time.sleep(request_delay())
    records = esummary_snp(nums)
    return envelope(
        source="dbsnp",
        mode="hgvs",
        label=hgvs,
        total=len(rsids),
        returned=len(records),
        records=[format_snp_record(r, detail=True) for r in records],
        extra={"rsids": rsids[:50]},
    )


def run_search(label: str, term: str, *, detail: bool = False, retmax: int = DEFAULT_RETMAX) -> str:
    print(f"【dbSNP 查询】{label}")
    print(f"  检索式：{term}")
    ids, total = esearch_snp(term, retmax=retmax)
    if not ids:
        print("未查询到匹配记录")
        return "未查询到"
    time.sleep(request_delay())
    records = esummary_snp(ids[: max(DISPLAY_LIMIT, min(len(ids), 20))])
    print_records(records[:DISPLAY_LIMIT], detail=detail)
    print_summary(total, min(DISPLAY_LIMIT, len(records)))
    clinical = records[0].get("clinical_significance") if records else None
    if clinical not in (None, "", "N/A", "unknown"):
        print("\n提示：该 SNP 有 ClinVar 临床标注，如需致病性详情请查 ClinVar。")
    return "查询完成"


def query_by_rsid(rsid: str) -> str:
    rsid = normalize_rsid(rsid)
    term = f"{rsid}[RS]"
    print(f"【dbSNP 查询】rsID：{rsid}")
    print(f"  检索式：{term}")
    ids, _ = esearch_snp(term, retmax=10)
    if not ids:
        print("未查询到该 rsID")
        return "未找到"
    time.sleep(request_delay())
    records = esummary_snp(ids)
    records = pick_rsid_record(records, rsid)
    print_records(records[:DISPLAY_LIMIT], detail=True)
    clinical = records[0].get("clinical_significance", "N/A") if records else "N/A"
    if clinical not in ("N/A", "", "unknown", "None", None):
        print("\n提示：该 SNP 有 ClinVar 临床标注，如需致病性详情请查 ClinVar。")
        print("      人群频率详情可联动 gnomAD skill。")
    return "查询完成"


def query_by_gene(gene: str) -> str:
    term = f"{gene}[GENE]"
    return run_search(f"基因变异：{gene}", term, detail=True)


def query_by_region(region: str, assembly: str = "GRCh38") -> str:
    term = parse_region(region, assembly=assembly)
    return run_search(f"基因组区域：{region} ({assembly})", term, detail=True)


def query_by_coord(chrom: str, pos: str, assembly: str = "GRCh38") -> str:
    pos_field = "POSITION" if assembly.upper() == "GRCH38" else "POSITION_GRCH37"
    term = f"{chrom}[CHR] AND {pos}[{pos_field}]"
    label = f"坐标：chr{chrom}:{pos} ({assembly})"
    print(f"【dbSNP 查询】{label}")
    print(f"  检索式：{term}")
    ids, total = esearch_snp(term, retmax=20)
    if not ids:
        print("该坐标未找到 dbSNP 记录")
        return "未查询到"
    time.sleep(request_delay())
    records = esummary_snp(ids)
    target_pos = str(pos)
    if assembly.upper() == "GRCH38":
        matched = [r for r in records if str(r.get("chrpos", "")).endswith(target_pos) or target_pos in str(r.get("chrpos", ""))]
    else:
        matched = [r for r in records if target_pos in str(r.get("chrpos_prev_assm", ""))]
    records = matched or records
    print_records(records[:DISPLAY_LIMIT], detail=True)
    print_summary(total, min(DISPLAY_LIMIT, len(records)))
    return "查询完成"


def query_clinical(gene: str) -> str:
    term = f'{gene}[GENE] AND ("pathogenic"[CLIN] OR "likely pathogenic"[CLIN])'
    return run_search(f"基因致病相关 SNP：{gene}", term, detail=True)


def query_rare(gene: str) -> str:
    term = f"{gene}[GENE] AND 00000.0000:00000.00999[GLOBAL_MAF]"
    return run_search(f"基因罕见变异 (MAF<0.01)：{gene}", term, detail=True)


def query_common(gene: str) -> str:
    term = f"{gene}[GENE] AND 00000.0100:00001.0000[GLOBAL_MAF]"
    return run_search(f"基因常见变异 (MAF≥0.01)：{gene}", term, detail=True)


def query_function(gene: str, fxn: str) -> str:
    fxn_term = fxn if "variant" in fxn.lower() else f"{fxn}_variant"
    term = f'{gene}[GENE] AND "{fxn_term}"[Function Class]'
    return run_search(f"基因功能类型 {fxn}：{gene}", term, detail=True)


def query_batch(rsids: list[str]) -> str:
    normalized = [normalize_rsid(r) for r in rsids]
    numbers = [rsid_number(r) for r in normalized]
    term = ",".join(numbers)
    print(f"【dbSNP 批量查询】{len(normalized)} 个 rsID")
    print(f"  检索式：{term}")
    ids, total = esearch_snp(term, retmax=len(numbers) + 5)
    if not ids:
        print("未查询到任何 rsID")
        return "未查询到"
    time.sleep(request_delay())
    records = esummary_snp(ids)
    by_num = {str(r.get("snp_id", "")): r for r in records}
    print(f"\n{'rsID':<16} {'坐标(GRCh38)':<22} {'基因':<10} {'功能类型':<30} {'MAF/频率'}")
    print("-" * 100)
    for rsid, num in zip(normalized, numbers):
        rec = by_num.get(num)
        if not rec:
            print(f"{rsid:<16} {'未找到':<22}")
            continue
        info = format_snp_record(rec)
        coord = _format_coord(rec)
        fxn = info["功能类型"][:28]
        print(f"{rsid:<16} {coord:<22} {info['基因']:<10} {fxn:<30} {info['MAF/频率'][:30]}")
    print(f"\n共查询 {len(normalized)} 个，匹配 {len(records)} 条")
    return "查询完成"


def query_by_ss(ss_id: str) -> str:
    ss_id = ss_id.strip()
    if not ss_id.lower().startswith("ss"):
        ss_id = f"ss{ss_id}"
    term = f"{ss_id}[SS]"
    return run_search(f"Submitter SNP：{ss_id}", term, detail=True)


def query_stats(gene: str) -> str:
    print(f"【dbSNP 统计】基因：{gene}")
    _, total_str = esearch_snp(f"{gene}[GENE]", retmax=0)
    total = int(total_str) if str(total_str).isdigit() else 0

    counts: dict[str, int] = {}
    for label, cls_term in SNP_CLASS_QUERIES.items():
        term = f"{gene}[GENE] AND {cls_term}"
        _, count_str = esearch_snp(term, retmax=0)
        counts[label] = int(count_str) if str(count_str).isdigit() else 0
        time.sleep(request_delay())

    extra_queries = {
        "致病相关(CLIN)": f'{gene}[GENE] AND ("pathogenic"[CLIN] OR "likely pathogenic"[CLIN])',
        "罕见(MAF<0.01)": f"{gene}[GENE] AND 00000.0000:00000.00999[GLOBAL_MAF]",
        "常见(MAF≥0.01)": f"{gene}[GENE] AND 00000.0100:00001.0000[GLOBAL_MAF]",
    }
    extra: dict[str, int] = {}
    for label, term in extra_queries.items():
        _, count_str = esearch_snp(term, retmax=0)
        extra[label] = int(count_str) if str(count_str).isdigit() else 0
        time.sleep(request_delay())

    print(f"\n基因 {gene} dbSNP 变异统计（共 {total} 条 RefSNP）")
    print(f"{'变异类型':<16} {'数量':>8} {'占比':>8}")
    print("-" * 36)
    for label, n in counts.items():
        pct = f"{100 * n / total:.1f}%" if total else "0%"
        print(f"{label:<16} {n:>8} {pct:>8}")

    print(f"\n{'分类':<20} {'数量':>8}")
    print("-" * 30)
    for label, n in extra.items():
        print(f"{label:<20} {n:>8}")

    print("\n提示：dbSNP 频率为各研究汇总；精确人群 AF 建议联动 gnomAD skill。")
    return "查询完成"


def _build_coord_json(chrom: str, pos: str, assembly: str) -> dict:
    pos_field = "POSITION" if assembly.upper() == "GRCH38" else "POSITION_GRCH37"
    term = f"{chrom}[CHR] AND {pos}[{pos_field}]"
    ids, total = esearch_snp(term, retmax=20)
    if not ids:
        return envelope(
            source="dbsnp", mode="coord", ok=False, label=f"chr{chrom}:{pos}",
            message="该坐标未找到 dbSNP 记录",
        )
    time.sleep(request_delay())
    records = esummary_snp(ids)
    target_pos = str(pos)
    if assembly.upper() == "GRCH38":
        matched = [r for r in records if str(r.get("chrpos", "")).endswith(target_pos) or target_pos in str(r.get("chrpos", ""))]
    else:
        matched = [r for r in records if target_pos in str(r.get("chrpos_prev_assm", ""))]
    records = matched or records
    rec = format_snp_record(records[0], detail=True) if records else {}
    total_n = int(total) if str(total).isdigit() else len(records)
    return envelope(
        source="dbsnp",
        mode="coord",
        label=f"chr{chrom}:{pos}",
        total=total_n,
        returned=1 if rec else 0,
        record=rec,
        extra={"assembly": assembly},
    )


def build_search_json(
    label: str, term: str, mode: str, *, detail: bool = False, retmax: int = DEFAULT_RETMAX
) -> dict:
    ids, total = esearch_snp(term, retmax=retmax)
    if not ids:
        return envelope(source="dbsnp", mode=mode, ok=False, label=label, message="未查询到匹配记录")
    time.sleep(request_delay())
    show_n = min(retmax, len(ids), 50)
    records = esummary_snp(ids[:show_n])
    total_n = int(total) if str(total).isdigit() else len(records)
    return envelope(
        source="dbsnp",
        mode=mode,
        label=label,
        total=total_n,
        returned=len(records),
        records=[format_snp_record(r, detail=detail) for r in records],
        extra={"term": term},
    )


def build_rsid_json(rsid: str) -> dict:
    rsid = normalize_rsid(rsid)
    term = f"{rsid}[RS]"
    ids, _ = esearch_snp(term, retmax=10)
    if not ids:
        return envelope(source="dbsnp", mode="rsid", ok=False, label=rsid, message="未查询到该 rsID")
    time.sleep(request_delay())
    records = esummary_snp(ids)
    records = pick_rsid_record(records, rsid)
    if not records:
        return envelope(source="dbsnp", mode="rsid", ok=False, label=rsid, message="未查询到该 rsID")
    rec = format_snp_record(records[0], detail=True)
    return envelope(source="dbsnp", mode="rsid", label=rsid, total=1, returned=1, record=rec)


def build_stats_json(gene: str) -> dict:
    _, total_str = esearch_snp(f"{gene}[GENE]", retmax=0)
    total = int(total_str) if str(total_str).isdigit() else 0
    counts: dict[str, int] = {}
    for label, cls_term in SNP_CLASS_QUERIES.items():
        term = f"{gene}[GENE] AND {cls_term}"
        _, count_str = esearch_snp(term, retmax=0)
        counts[label] = int(count_str) if str(count_str).isdigit() else 0
        time.sleep(request_delay())
    extra: dict[str, int] = {}
    for label, term in {
        "致病相关(CLIN)": f'{gene}[GENE] AND ("pathogenic"[CLIN] OR "likely pathogenic"[CLIN])',
        "罕见(MAF<0.01)": f"{gene}[GENE] AND 00000.0000:00000.00999[GLOBAL_MAF]",
        "常见(MAF≥0.01)": f"{gene}[GENE] AND 00000.0100:00001.0000[GLOBAL_MAF]",
    }.items():
        _, count_str = esearch_snp(term, retmax=0)
        extra[label] = int(count_str) if str(count_str).isdigit() else 0
        time.sleep(request_delay())
    return envelope(
        source="dbsnp",
        mode="stats",
        label=gene,
        total=total,
        returned=len(counts),
        truncated=False,
        extra={"gene": gene, "counts": counts, "extra": extra},
    )


def build_batch_json(rsids: list[str]) -> dict:
    normalized = [normalize_rsid(r) for r in rsids]
    numbers = [rsid_number(r) for r in normalized]
    ids, total = esearch_snp(",".join(numbers), retmax=len(numbers) + 5)
    if not ids:
        return envelope(source="dbsnp", mode="batch", ok=False, message="未查询到任何 rsID")
    time.sleep(request_delay())
    records = esummary_snp(ids)
    by_num = {str(r.get("snp_id", "")): r for r in records}
    rows = []
    for rsid, num in zip(normalized, numbers):
        rec = by_num.get(num)
        rows.append(
            {
                "rsid": rsid,
                "found": bool(rec),
                "record": format_snp_record(rec, detail=True) if rec else None,
            }
        )
    total_n = int(total) if str(total).isdigit() else len(rows)
    return envelope(
        source="dbsnp",
        mode="batch",
        total=total_n,
        returned=len(rows),
        records=rows,
    )




def main() -> None:
    # Backward compatibility: python query.py rs80357906
    if len(sys.argv) == 2 and re.match(r"^rs?\d+$", sys.argv[1], re.I):
        query_by_rsid(sys.argv[1])
        return

    parser = argparse.ArgumentParser(description="Query dbSNP via NCBI E-utilities")
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--format", choices=["text", "json"], default="text")
    parent.add_argument("--retmax", type=int, default=DEFAULT_RETMAX)
    sub = parser.add_subparsers(dest="mode")

    rsid_p = sub.add_parser("rsid", parents=[parent], help="Query SNP by rsID")
    rsid_p.add_argument("rsid", help="rsID, e.g. rs80357906")

    gene_p = sub.add_parser("gene", parents=[parent], help="List variants in a gene")
    gene_p.add_argument("gene", help="Gene symbol, e.g. BRCA1")

    region_p = sub.add_parser("region", parents=[parent], help="Variants in a genomic region")
    region_p.add_argument("region", help="chr17:43057060-43057065 or '17 43057060 43057065'")
    region_p.add_argument("--assembly", default="GRCh38", choices=["GRCh38", "GRCh37"])

    coord_p = sub.add_parser("coord", parents=[parent], help="Lookup rsID by chromosome coordinate")
    coord_p.add_argument("chrom", help="Chromosome, e.g. 17")
    coord_p.add_argument("pos", help="Base position")
    coord_p.add_argument("--assembly", default="GRCh38", choices=["GRCh38", "GRCh37"])

    clinical_p = sub.add_parser("clinical", parents=[parent], help="Pathogenic/likely pathogenic SNPs in gene")
    clinical_p.add_argument("gene", help="Gene symbol")

    rare_p = sub.add_parser("rare", parents=[parent], help="Rare variants in gene (MAF < 0.01)")
    rare_p.add_argument("gene", help="Gene symbol")

    common_p = sub.add_parser("common", parents=[parent], help="Common variants in gene (MAF >= 0.01)")
    common_p.add_argument("gene", help="Gene symbol")

    fxn_p = sub.add_parser("function", parents=[parent], help="Variants by function class in gene")
    fxn_p.add_argument("gene", help="Gene symbol")
    fxn_p.add_argument("fxn", help="Function class, e.g. missense, frameshift, synonymous")

    batch_p = sub.add_parser("batch", parents=[parent], help="Batch lookup multiple rsIDs")
    batch_p.add_argument("rsids", nargs="+", help="rsIDs to query")

    ss_p = sub.add_parser("ss", parents=[parent], help="Lookup by Submitter SNP ID (ss)")
    ss_p.add_argument("ss_id", help="ss ID, e.g. ss66803666")

    stats_p = sub.add_parser("stats", parents=[parent], help="Variant type statistics for a gene")
    stats_p.add_argument("gene", help="Gene symbol")

    hgvs_p = sub.add_parser("hgvs", parents=[parent], help="Resolve HGVS to rsID(s)")
    hgvs_p.add_argument("hgvs", help="HGVS string, e.g. NC_000017.11:g.43057062G>A or c.5266dup")

    args, unknown = parser.parse_known_args()
    if args.mode is None:
        parser.print_help()
        sys.exit(1)

    retmax = getattr(args, "retmax", DEFAULT_RETMAX)
    json_handlers = {
        "rsid": lambda: build_rsid_json(args.rsid),
        "gene": lambda: build_search_json(
            f"基因变异：{args.gene}", f"{args.gene}[GENE]", "gene", detail=True, retmax=retmax
        ),
        "region": lambda: build_search_json(
            f"基因组区域：{args.region} ({args.assembly})",
            parse_region(args.region, assembly=args.assembly),
            "region",
            detail=True,
            retmax=retmax,
        ),
        "coord": lambda: _build_coord_json(args.chrom, args.pos, args.assembly),
        "clinical": lambda: build_search_json(
            f"基因致病相关 SNP：{args.gene}",
            f'{args.gene}[GENE] AND ("pathogenic"[CLIN] OR "likely pathogenic"[CLIN])',
            "clinical",
            detail=True,
            retmax=retmax,
        ),
        "rare": lambda: build_search_json(
            f"基因罕见变异 (MAF<0.01)：{args.gene}",
            f"{args.gene}[GENE] AND 00000.0000:00000.00999[GLOBAL_MAF]",
            "rare",
            detail=True,
            retmax=retmax,
        ),
        "common": lambda: build_search_json(
            f"基因常见变异 (MAF≥0.01)：{args.gene}",
            f"{args.gene}[GENE] AND 00000.0100:00001.0000[GLOBAL_MAF]",
            "common",
            detail=True,
            retmax=retmax,
        ),
        "function": lambda: build_search_json(
            f"基因功能类型 {args.fxn}：{args.gene}",
            f'{args.gene}[GENE] AND "{args.fxn if "variant" in args.fxn.lower() else args.fxn + "_variant"}"[Function Class]',
            "function",
            detail=True,
            retmax=retmax,
        ),
        "stats": lambda: build_stats_json(args.gene),
        "hgvs": lambda: build_hgvs_json(args.hgvs),
        "batch": lambda: build_batch_json(args.rsids),
        "ss": lambda: build_search_json(
            f"Submitter SNP：{args.ss_id}",
            f"{args.ss_id if str(args.ss_id).lower().startswith('ss') else 'ss' + str(args.ss_id)}[SS]",
            "ss",
            detail=True,
            retmax=retmax,
        ),
    }

    if args.format == "json" and args.mode in json_handlers:
        try:
            emit_json(json_handlers[args.mode]())
        except ValueError as exc:
            emit_json(envelope(source="dbsnp", mode=args.mode, ok=False, message=str(exc)))
            sys.exit(1)
        except requests.RequestException as exc:
            emit_json(envelope(source="dbsnp", mode=args.mode, ok=False, message=f"API request failed: {exc}"))
            sys.exit(1)
        return

    handlers = {
        "rsid": lambda: query_by_rsid(args.rsid),
        "gene": lambda: query_by_gene(args.gene),
        "region": lambda: query_by_region(args.region, args.assembly),
        "coord": lambda: query_by_coord(args.chrom, args.pos, args.assembly),
        "clinical": lambda: query_by_clinical(args.gene),
        "rare": lambda: query_by_rare(args.gene),
        "common": lambda: query_by_common(args.gene),
        "function": lambda: query_function(args.gene, args.fxn),
        "batch": lambda: query_batch(args.rsids),
        "ss": lambda: query_by_ss(args.ss_id),
        "stats": lambda: query_stats(args.gene),
        "hgvs": lambda: query_by_hgvs(args.hgvs),
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
