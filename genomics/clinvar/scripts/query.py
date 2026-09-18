#!/usr/bin/env python3
"""Query ClinVar: evidence/retmax/JSON envelope + NCBI retry."""

from __future__ import annotations

import argparse
import re
import sys
import time
from collections import Counter
from pathlib import Path

import requests

_LIB = Path(__file__).resolve().parent / "_lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from ncbi_http import eutils_get, request_delay  # noqa: E402
from result import emit_json, envelope  # noqa: E402

DEFAULT_RETMAX = 20
DISPLAY_LIMIT = 5

PATHOGENIC_FILTER = (
    '(Pathogenic[Clinical Significance] OR "Likely pathogenic"[Clinical Significance])'
)
VUS_FILTER = '"Uncertain significance"[Clinical Significance]'
CONFLICT_FILTER = '"conflicting interpretations"[Clinical Significance]'
BENIGN_FILTER = (
    '(Benign[Clinical Significance] OR "Likely benign"[Clinical Significance])'
)

CLASSIFICATION_QUERIES = {
    "Pathogenic": "Pathogenic[Clinical Significance]",
    "Likely pathogenic": '"Likely pathogenic"[Clinical Significance]',
    "Uncertain significance": VUS_FILTER,
    "Likely benign": '"Likely benign"[Clinical Significance]',
    "Benign": "Benign[Clinical Significance]",
    "Conflicting": CONFLICT_FILTER,
}


def esearch_clinvar(term: str, retmax: int = DEFAULT_RETMAX) -> tuple[list[str], str]:
    result = eutils_get(
        "esearch.fcgi",
        {"db": "clinvar", "term": term, "retmode": "json", "retmax": retmax},
    ).get("esearchresult", {})
    return result.get("idlist", []), result.get("count", "0")


def esummary_clinvar(ids: list[str]) -> list[dict]:
    if not ids:
        return []
    result = eutils_get(
        "esummary.fcgi",
        {"db": "clinvar", "id": ",".join(ids), "retmode": "json"},
    ).get("result", {})
    uids = result.get("uids", [])
    return [result[uid] for uid in uids if uid in result]


def _extract_rsid(rec: dict) -> str:
    for var in rec.get("variation_set") or []:
        for xref in var.get("variation_xrefs") or []:
            if xref.get("db_source") == "dbSNP":
                rsid = xref.get("db_id", "")
                if rsid and not str(rsid).startswith("rs"):
                    return f"rs{rsid}"
                return str(rsid)
    return "N/A"


def _extract_coords(rec: dict) -> str:
    for var in rec.get("variation_set") or []:
        for loc in var.get("variation_loc") or []:
            if loc.get("assembly_name") == "GRCh38" and loc.get("status") == "current":
                return f"chr{loc.get('chr')}:{loc.get('start')}-{loc.get('stop')} (GRCh38)"
    for var in rec.get("variation_set") or []:
        for loc in var.get("variation_loc") or []:
            if loc.get("assembly_name") == "GRCh38":
                return f"chr{loc.get('chr')}:{loc.get('start')}-{loc.get('stop')} (GRCh38)"
    return "N/A"


def _extract_diseases(germline: dict) -> str:
    traits = germline.get("trait_set") or []
    names = [t.get("trait_name", "") for t in traits if t.get("trait_name")]
    return ", ".join(names) if names else "N/A"


def _extract_omim(germline: dict) -> str:
    omim_ids: list[str] = []
    for trait in germline.get("trait_set") or []:
        for xref in trait.get("trait_xrefs") or []:
            if xref.get("db_source") == "OMIM":
                omim_ids.append(xref.get("db_id", ""))
    return ", ".join(omim_ids) if omim_ids else "N/A"


def _submission_count(rec: dict) -> str:
    subs = rec.get("supporting_submissions") or {}
    scv = len(subs.get("scv") or [])
    rcv = len(subs.get("rcv") or [])
    if scv or rcv:
        return f"SCV {scv} / RCV {rcv}"
    return "N/A"


def format_record(rec: dict, *, detail: bool = False) -> dict[str, str]:
    germline = rec.get("germline_classification") or {}
    info = {
        "ClinVar ID": rec.get("accession_version") or rec.get("accession") or rec.get("uid", "N/A"),
        "变异": rec.get("title", "N/A"),
        "临床意义": germline.get("description") or "N/A",
        "评审状态": germline.get("review_status") or "N/A",
    }
    if detail:
        info.update(
            {
                "基因": rec.get("gene_sort", "N/A"),
                "坐标": _extract_coords(rec),
                "rsID": _extract_rsid(rec),
                "分子后果": ", ".join(rec.get("molecular_consequence_list") or []) or "N/A",
                "蛋白变化": rec.get("protein_change") or "N/A",
                "关联疾病": _extract_diseases(germline),
                "OMIM": _extract_omim(germline),
                "最后评估": germline.get("last_evaluated") or "N/A",
                "提交数": _submission_count(rec),
            }
        )
    return info


def extract_evidence(rec: dict) -> dict:
    """Deeper summary fields for evidence mode (submitters / traits / review)."""
    germline = rec.get("germline_classification") or {}
    subs = rec.get("supporting_submissions") or {}
    scv = list(subs.get("scv") or [])
    rcv = list(subs.get("rcv") or [])
    traits = []
    for t in germline.get("trait_set") or []:
        traits.append(
            {
                "name": t.get("trait_name"),
                "xrefs": [
                    f"{x.get('db_source')}:{x.get('db_id')}"
                    for x in (t.get("trait_xrefs") or [])
                    if x.get("db_source")
                ],
            }
        )
    return {
        **format_record(rec, detail=True),
        "review_status": germline.get("review_status"),
        "last_evaluated": germline.get("last_evaluated"),
        "scv_accessions": scv[:20],
        "rcv_accessions": rcv[:20],
        "submission_counts": {"scv": len(scv), "rcv": len(rcv)},
        "traits": traits,
        "molecular_consequence": list(rec.get("molecular_consequence_list") or []),
    }


def print_records(records: list[dict], *, detail: bool = False) -> None:
    for i, rec in enumerate(records, 1):
        info = format_record(rec, detail=detail)
        print(f"\n===== 结果 {i} =====")
        for k, v in info.items():
            print(f"  {k}: {v}")


def print_summary(total: str | int, shown: int) -> None:
    total_n = int(total) if str(total).isdigit() else shown
    print(f"\n共检索到 {total_n} 条，展示前 {shown} 条")


def normalize_rsid(rsid: str) -> str:
    rsid = rsid.strip()
    if not rsid.lower().startswith("rs"):
        rsid = f"rs{rsid}"
    return rsid


def parse_region(region_arg: str) -> str:
    """Parse chr:start-end or chr start end into ClinVar esearch term."""
    region_arg = region_arg.strip()
    m = re.match(r"^(?:chr)?(\d+|X|Y|MT)[:\s-]+(\d+)[:\s-]+(\d+)$", region_arg, re.I)
    if m:
        chrom, start, end = m.group(1), m.group(2), m.group(3)
        if int(start) > int(end):
            start, end = end, start
        return f"{chrom}[chr] AND {start}:{end}[chrpos38]"
    m = re.match(r"^(\d+|X|Y|MT)\s+(\d+)\s+(\d+)$", region_arg, re.I)
    if m:
        chrom, start, end = m.group(1), m.group(2), m.group(3)
        if int(start) > int(end):
            start, end = end, start
        return f"{chrom}[chr] AND {start}:{end}[chrpos38]"
    if re.match(r"^chr\d+:\d+-\d+$", region_arg, re.I):
        return region_arg
    raise ValueError(f"无法解析区域格式：{region_arg}（示例：chr17:43044295-43044305 或 17 43044295 43044305）")


def run_search(
    label: str,
    term: str,
    *,
    detail: bool = False,
    retmax: int = DEFAULT_RETMAX,
    display_limit: int | None = None,
) -> str:
    show_n = display_limit if display_limit is not None else min(retmax, 50)
    print(f"【ClinVar 查询】{label}")
    print(f"  检索式：{term}")
    var_ids, total = esearch_clinvar(term, retmax=retmax)
    if not var_ids:
        print("未查询到匹配记录")
        return "未查询到"
    time.sleep(request_delay())
    shown_ids = var_ids[:show_n]
    records = esummary_clinvar(shown_ids)
    print_records(records, detail=detail)
    total_n = int(total) if str(total).isdigit() else len(records)
    print(f"\n共检索到 {total_n} 条，返回 {len(records)} 条"
          f"{'（已截断）' if len(records) < total_n else ''}")
    return "查询完成"


def query_evidence(query: str, *, retmax: int = 5) -> str:
    query = query.strip()
    if query.isdigit() or re.match(r"^VCV\d+", query, re.I):
        if query.isdigit():
            term = query
        elif re.match(r"^VCV\d+", query, re.I):
            term = f"{query}[clv_acc]"
        else:
            term = f"VCV{query}[clv_acc]"
        label = f"evidence：{query}"
    elif re.match(r"^rs?\d+$", query, re.I):
        term = f"{normalize_rsid(query)}[rs]"
        label = f"evidence rsID：{normalize_rsid(query)}"
    else:
        term = f"{query}[gene] AND {PATHOGENIC_FILTER}"
        label = f"evidence gene：{query}"
    print(f"【ClinVar evidence】{label}")
    print(f"  检索式：{term}")
    var_ids, total = esearch_clinvar(term, retmax=retmax)
    if not var_ids:
        print("未查询到匹配记录")
        return "未查询到"
    time.sleep(request_delay())
    records = esummary_clinvar(var_ids[:DISPLAY_LIMIT])
    for i, rec in enumerate(records, 1):
        ev = extract_evidence(rec)
        print(f"\n===== evidence {i} =====")
        for k, v in ev.items():
            print(f"  {k}: {v}")
    total_n = int(total) if str(total).isdigit() else len(records)
    print(f"\n共检索到 {total_n} 条，返回 {len(records)} 条")
    return "查询完成"


def query_by_gene(gene: str, *, retmax: int = DEFAULT_RETMAX) -> str:
    term = f"{gene}[gene] AND {PATHOGENIC_FILTER}"
    return run_search(f"基因致病位点：{gene}", term, detail=True, retmax=retmax)


def query_by_rsid(rsid: str, *, retmax: int = DEFAULT_RETMAX) -> str:
    rsid = normalize_rsid(rsid)
    term = f"{rsid}[rs]"
    return run_search(f"变异：{rsid}", term, detail=True, retmax=retmax)


def query_by_disease(disease: str, *, pathogenic_only: bool = True, retmax: int = DEFAULT_RETMAX) -> str:
    term = f"{disease}[dis]"
    if pathogenic_only:
        term += f" AND {PATHOGENIC_FILTER}"
    return run_search(f"疾病相关变异：{disease}", term, detail=True, retmax=retmax)


def _hgvs_matches(rec: dict, hgvs: str) -> bool:
    hgvs_lower = hgvs.lower()
    title = (rec.get("title") or "").lower()
    if hgvs_lower in title:
        return True
    for var in rec.get("variation_set") or []:
        cdna = (var.get("cdna_change") or "").lower()
        name = (var.get("variation_name") or "").lower()
        if hgvs_lower in cdna or hgvs_lower in name:
            return True
    return False


def query_by_hgvs(hgvs: str, gene: str | None = None) -> str:
    hgvs = hgvs.strip()
    term = f'"{hgvs}"[varnam]' if re.search(r"[cgp]\.", hgvs, re.I) else f"{hgvs}[varnam]"
    if gene:
        term += f" AND {gene}[gene]"
    label = f"HGVS：{hgvs}" + (f"（{gene}）" if gene else "")
    print(f"【ClinVar 查询】{label}")
    print(f"  检索式：{term}")
    var_ids, total = esearch_clinvar(term, retmax=50)
    if not var_ids:
        print("未查询到匹配记录")
        return "未查询到"
    time.sleep(request_delay())
    records = esummary_clinvar(var_ids)
    matched = [rec for rec in records if _hgvs_matches(rec, hgvs)]
    if not matched:
        matched = records
        print("  提示：未找到精确 HGVS 匹配，展示模糊检索结果")
    else:
        total = str(len(matched))
    print_records(matched[:DISPLAY_LIMIT], detail=True)
    print_summary(total, min(DISPLAY_LIMIT, len(matched)))
    return "查询完成"


def query_by_region(region: str, *, retmax: int = DEFAULT_RETMAX) -> str:
    term = parse_region(region)
    return run_search(f"基因组区域：{region}", term, detail=True, retmax=retmax)


def query_vus(gene: str, *, retmax: int = DEFAULT_RETMAX) -> str:
    term = f"{gene}[gene] AND {VUS_FILTER}"
    return run_search(f"基因 VUS：{gene}", term, detail=True, retmax=retmax)


def query_conflict(gene: str | None = None, *, retmax: int = DEFAULT_RETMAX) -> str:
    term = CONFLICT_FILTER
    if gene:
        term = f"{gene}[gene] AND {term}"
    label = f"解读冲突：{gene}" if gene else "解读冲突（全局）"
    return run_search(label, term, detail=True, retmax=retmax)


def query_stats(gene: str) -> str:
    print(f"【ClinVar 统计】基因：{gene}")
    counts: Counter[str] = Counter()
    total = 0
    for label, cls_term in CLASSIFICATION_QUERIES.items():
        term = f"{gene}[gene] AND {cls_term}"
        _, count_str = esearch_clinvar(term, retmax=0)
        count = int(count_str) if str(count_str).isdigit() else 0
        counts[label] = count
        total += count
        time.sleep(request_delay())

    all_ids, all_count = esearch_clinvar(f"{gene}[gene]", retmax=0)
    total_all = int(all_count) if str(all_count).isdigit() else total

    print(f"\n基因 {gene} ClinVar 变异分类统计（共 {total_all} 条记录）")
    print("说明：ClinVar 按「变异-疾病」对存储记录，同一变异可出现在多个分类中，占比之和可能 >100%。")
    print(f"{'分类':<24} {'数量':>8} {'占比':>8}")
    print("-" * 44)
    for label in CLASSIFICATION_QUERIES:
        n = counts[label]
        pct = f"{100 * n / total_all:.1f}%" if total_all else "0%"
        print(f"{label:<24} {n:>8} {pct:>8}")

    pathogenic_n = counts["Pathogenic"] + counts["Likely pathogenic"]
    vus_n = counts["Uncertain significance"]
    conflict_n = counts["Conflicting"]
    print(f"\n摘要：致病/可能致病 {pathogenic_n} 条，VUS {vus_n} 条，解读冲突 {conflict_n} 条")
    if conflict_n:
        print("提示：存在解读冲突变异，建议用 conflict 子命令查看详情。")
    return "查询完成"


def query_by_vcv(vcv: str) -> str:
    vcv = vcv.strip()
    if vcv.isdigit():
        term = vcv
        label = f"Variation ID：{vcv}"
    elif re.match(r"^VCV\d+", vcv, re.I):
        term = f"{vcv}[clv_acc]"
        label = f"VCV：{vcv}"
    else:
        term = f"VCV{vcv}[clv_acc]" if not vcv.upper().startswith("VCV") else f"{vcv}[clv_acc]"
        label = f"VCV：{vcv}"
    return run_search(label, term, detail=True, retmax=5)


def build_search_json(
    label: str,
    term: str,
    mode: str,
    *,
    detail: bool = True,
    retmax: int = DEFAULT_RETMAX,
) -> dict:
    var_ids, total = esearch_clinvar(term, retmax=retmax)
    if not var_ids:
        return envelope(
            source="clinvar", mode=mode, ok=False, label=label, message="未查询到匹配记录"
        )
    time.sleep(request_delay())
    show_n = min(retmax, len(var_ids), 50)
    records = esummary_clinvar(var_ids[:show_n])
    total_n = int(total) if str(total).isdigit() else len(records)
    return envelope(
        source="clinvar",
        mode=mode,
        label=label,
        total=total_n,
        returned=len(records),
        records=[format_record(r, detail=detail) for r in records],
        extra={"term": term},
    )


def build_rsid_json(rsid: str) -> dict:
    rsid = normalize_rsid(rsid)
    term = f"{rsid}[rs]"
    var_ids, total = esearch_clinvar(term, retmax=5)
    if not var_ids:
        return envelope(
            source="clinvar", mode="rsid", ok=False, label=rsid, message="未查询到该 rsID"
        )
    time.sleep(request_delay())
    records = esummary_clinvar(var_ids[:DISPLAY_LIMIT])
    rec = format_record(records[0], detail=True)
    total_n = int(total) if str(total).isdigit() else len(records)
    return envelope(
        source="clinvar",
        mode="rsid",
        label=rsid,
        total=total_n,
        returned=1,
        record=rec,
        extra={"interpretation": _interpret_significance(rec.get("临床意义", ""))},
    )


def build_evidence_json(query: str, *, retmax: int = 5) -> dict:
    query = query.strip()
    if query.isdigit():
        term = query
    elif re.match(r"^VCV\d+", query, re.I):
        term = f"{query}[clv_acc]"
    elif re.match(r"^rs?\d+$", query, re.I):
        term = f"{normalize_rsid(query)}[rs]"
    else:
        term = f"{query}[gene] AND {PATHOGENIC_FILTER}"
    var_ids, total = esearch_clinvar(term, retmax=retmax)
    if not var_ids:
        return envelope(
            source="clinvar", mode="evidence", ok=False, label=query, message="未查询到匹配记录"
        )
    time.sleep(request_delay())
    records = esummary_clinvar(var_ids[:DISPLAY_LIMIT])
    total_n = int(total) if str(total).isdigit() else len(records)
    return envelope(
        source="clinvar",
        mode="evidence",
        label=query,
        total=total_n,
        returned=len(records),
        records=[extract_evidence(r) for r in records],
        extra={"term": term},
    )


def _interpret_significance(sig: str) -> str:
    s = (sig or "").lower()
    if "pathogenic" in s and "likely" not in s and "conflict" not in s:
        return "pathogenic — correlate with other evidence"
    if "likely pathogenic" in s:
        return "likely pathogenic — further validation recommended"
    if "uncertain" in s or "vus" in s:
        return "VUS — do not state as pathogenic"
    if "conflict" in s:
        return "conflicting interpretations — review submitter evidence"
    if "benign" in s:
        return "benign / likely benign"
    return "interpret with review status and corroborating evidence"


def build_stats_json(gene: str) -> dict:
    counts: Counter[str] = Counter()
    for label, cls_term in CLASSIFICATION_QUERIES.items():
        term = f"{gene}[gene] AND {cls_term}"
        _, count_str = esearch_clinvar(term, retmax=0)
        counts[label] = int(count_str) if str(count_str).isdigit() else 0
        time.sleep(request_delay())
    _, all_count = esearch_clinvar(f"{gene}[gene]", retmax=0)
    total_all = int(all_count) if str(all_count).isdigit() else sum(counts.values())
    pathogenic_n = counts["Pathogenic"] + counts["Likely pathogenic"]
    vus_n = counts["Uncertain significance"]
    conflict_n = counts["Conflicting"]
    return envelope(
        source="clinvar",
        mode="stats",
        label=gene,
        total=total_all,
        returned=len(counts),
        truncated=False,
        extra={
            "gene": gene,
            "counts": dict(counts),
            "summary": (
                f"pathogenic/likely_pathogenic={pathogenic_n}, "
                f"VUS={vus_n}, conflicting={conflict_n}"
            ),
        },
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Query ClinVar via NCBI E-utilities")
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--format", choices=["text", "json"], default="text")
    parent.add_argument("--retmax", type=int, default=DEFAULT_RETMAX, help="esearch retmax")
    sub = parser.add_subparsers(dest="mode", required=True)

    gene_p = sub.add_parser("gene", parents=[parent], help="Pathogenic variants by gene symbol")
    gene_p.add_argument("gene", help="Gene symbol, e.g. BRCA1")

    rsid_p = sub.add_parser("rsid", parents=[parent], help="Clinical significance by rsID")
    rsid_p.add_argument("rsid", help="rsID, e.g. rs80357906")

    dis_p = sub.add_parser("disease", parents=[parent], help="Variants associated with a disease/phenotype")
    dis_p.add_argument("disease", help="Disease keyword")
    dis_p.add_argument("--all", action="store_true", help="Include all classifications")

    hgvs_p = sub.add_parser("hgvs", parents=[parent], help="Lookup by HGVS or variant name")
    hgvs_p.add_argument("hgvs", help="HGVS fragment")
    hgvs_p.add_argument("--gene", help="Optional gene symbol")

    region_p = sub.add_parser("region", parents=[parent], help="Variants in a genomic region (GRCh38)")
    region_p.add_argument("region", help="Region string")

    vus_p = sub.add_parser("vus", parents=[parent], help="VUS for a gene")
    vus_p.add_argument("gene", help="Gene symbol")

    conflict_p = sub.add_parser("conflict", parents=[parent], help="Conflicting interpretations")
    conflict_p.add_argument("gene", nargs="?", help="Optional gene symbol")

    stats_p = sub.add_parser("stats", parents=[parent], help="Classification counts for a gene")
    stats_p.add_argument("gene", help="Gene symbol")

    vcv_p = sub.add_parser("vcv", parents=[parent], help="Lookup by Variation ID or VCV")
    vcv_p.add_argument("vcv", help="Variation ID or VCV accession")

    ev_p = sub.add_parser("evidence", parents=[parent], help="Deeper submitter/trait evidence")
    ev_p.add_argument("query", help="Gene, rsID, Variation ID, or VCV")

    args = parser.parse_args()
    retmax = getattr(args, "retmax", DEFAULT_RETMAX)

    def _hgvs_json() -> dict:
        hgvs = args.hgvs.strip()
        term = f'"{hgvs}"[varnam]' if re.search(r"[cgp]\.", hgvs, re.I) else f"{hgvs}[varnam]"
        if args.gene:
            term += f" AND {args.gene}[gene]"
        return build_search_json(f"HGVS：{hgvs}", term, "hgvs", retmax=max(retmax, 50))

    def _vcv_json() -> dict:
        vcv = args.vcv.strip()
        if vcv.isdigit():
            term = vcv
        elif re.match(r"^VCV\d+", vcv, re.I):
            term = f"{vcv}[clv_acc]"
        else:
            term = f"VCV{vcv}[clv_acc]" if not vcv.upper().startswith("VCV") else f"{vcv}[clv_acc]"
        return build_search_json(f"VCV：{vcv}", term, "vcv", retmax=min(retmax, 5))

    json_handlers = {
        "gene": lambda: build_search_json(
            f"基因致病位点：{args.gene}",
            f"{args.gene}[gene] AND {PATHOGENIC_FILTER}",
            "gene",
            retmax=retmax,
        ),
        "rsid": lambda: build_rsid_json(args.rsid),
        "disease": lambda: build_search_json(
            f"疾病相关变异：{args.disease}",
            f"{args.disease}[dis]" + ("" if args.all else f" AND {PATHOGENIC_FILTER}"),
            "disease",
            retmax=retmax,
        ),
        "hgvs": _hgvs_json,
        "region": lambda: build_search_json(
            f"基因组区域：{args.region}", parse_region(args.region), "region", retmax=retmax
        ),
        "vus": lambda: build_search_json(
            f"基因 VUS：{args.gene}", f"{args.gene}[gene] AND {VUS_FILTER}", "vus", retmax=retmax
        ),
        "conflict": lambda: build_search_json(
            f"解读冲突：{args.gene}" if args.gene else "解读冲突（全局）",
            f"{args.gene}[gene] AND {CONFLICT_FILTER}" if args.gene else CONFLICT_FILTER,
            "conflict",
            retmax=retmax,
        ),
        "stats": lambda: build_stats_json(args.gene),
        "vcv": _vcv_json,
        "evidence": lambda: build_evidence_json(args.query, retmax=min(retmax, 5)),
    }

    if args.format == "json":
        try:
            emit_json(json_handlers[args.mode]())
        except ValueError as exc:
            emit_json(envelope(source="clinvar", mode=args.mode, ok=False, message=str(exc)))
            sys.exit(1)
        except requests.RequestException as exc:
            emit_json(envelope(source="clinvar", mode=args.mode, ok=False, message=f"API request failed: {exc}"))
            sys.exit(1)
        return

    handlers = {
        "gene": lambda: query_by_gene(args.gene, retmax=retmax),
        "rsid": lambda: query_by_rsid(args.rsid, retmax=retmax),
        "disease": lambda: query_by_disease(args.disease, pathogenic_only=not args.all, retmax=retmax),
        "hgvs": lambda: query_by_hgvs(args.hgvs, args.gene),
        "region": lambda: query_by_region(args.region, retmax=retmax),
        "vus": lambda: query_vus(args.gene, retmax=retmax),
        "conflict": lambda: query_conflict(args.gene, retmax=retmax),
        "stats": lambda: query_stats(args.gene),
        "vcv": lambda: query_by_vcv(args.vcv),
        "evidence": lambda: query_evidence(args.query, retmax=min(retmax, 5)),
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
