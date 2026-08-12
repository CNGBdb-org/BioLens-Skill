#!/usr/bin/env python3
"""Query NCBI GEO / SRA / BioProject — single-cell data discovery entry point.

This skill finds datasets and download paths. It does not run scRNA-seq analysis.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import requests

_LIB = Path(__file__).resolve().parent / "_lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from ncbi_http import EUTILS, eutils_get, http_get, request_delay  # noqa: E402

GEO_ACC = "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi"
DISPLAY_LIMIT = 8

SC_HINT = (
    '("single cell"[All Fields] OR "single-cell"[All Fields] OR scRNA-seq[All Fields] '
    'OR snRNA-seq[All Fields] OR "spatial transcriptomics"[All Fields] OR 10x[All Fields])'
)


def _sleep() -> None:
    time.sleep(request_delay())


def _get_json(path: str, **params: Any) -> dict:
    _sleep()
    params = {**params, "retmode": "json"}
    return eutils_get(path, params, timeout=60)


def _get_text(path: str, **params: Any) -> str:
    _sleep()
    r = http_get(f"{EUTILS}/{path}", params=params, timeout=60)
    return r.text


def esearch(db: str, term: str, retmax: int = DISPLAY_LIMIT) -> tuple[list[str], str]:
    data = _get_json("esearch.fcgi", db=db, term=term, retmax=retmax)
    result = data.get("esearchresult", {})
    return result.get("idlist", []), result.get("count", "0")


def esummary(db: str, ids: list[str]) -> list[dict]:
    if not ids:
        return []
    data = _get_json("esummary.fcgi", db=db, id=",".join(ids))
    result = data.get("result", {})
    uids = result.get("uids", [])
    return [result[uid] for uid in uids if uid in result]


def elink_ids(dbfrom: str, db: str, uid: str) -> list[str]:
    data = _get_json("elink.fcgi", dbfrom=dbfrom, db=db, id=uid)
    out: list[str] = []
    for linkset in data.get("linksets", []):
        for ldb in linkset.get("linksetdbs") or []:
            out.extend(ldb.get("links") or [])
    return out


def fetch_geo_soft(accession: str, view: str = "quick", retries: int = 3) -> str:
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            _sleep()
            r = http_get(
                GEO_ACC,
                params={"acc": accession, "targ": "self", "form": "text", "view": view},
                timeout=60,
            )
            text = r.text
            if "SoftError" in text or text.strip().startswith("Error"):
                raise ValueError(f"GEO 未找到登录号：{accession}")
            return text
        except (requests.RequestException, ValueError) as exc:
            last_err = exc
            if isinstance(exc, ValueError) and "未找到" in str(exc):
                raise
            time.sleep(request_delay() * (attempt + 2))
    assert last_err is not None
    raise last_err


def parse_soft(text: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = defaultdict(list)
    for raw in text.splitlines():
        line = raw.strip().rstrip("\r")
        if not line.startswith("!"):
            continue
        if " = " not in line:
            continue
        key, val = line[1:].split(" = ", 1)
        fields[key].append(val.strip())
    return fields


def first(fields: dict[str, list[str]], *keys: str, default: str = "N/A") -> str:
    for key in keys:
        vals = fields.get(key)
        if vals:
            return vals[0]
    return default


def all_vals(fields: dict[str, list[str]], *keys: str) -> list[str]:
    out: list[str] = []
    for key in keys:
        out.extend(fields.get(key) or [])
    return out


def truncate(text: str, n: int = 320) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    if len(text) <= n:
        return text
    return text[: n - 1] + "…"


def extract_accessions(text: str) -> dict[str, list[str]]:
    patterns = {
        "BioProject": r"PRJ[NED][A-Z]\d+",
        "BioSample": r"SAM[NED][A-Z]?\d+",
        "SRA_Study": r"SRP\d+",
        "SRA_Experiment": r"SRX\d+",
        "SRA_Run": r"SRR\d+",
        "EGA": r"EGA[SS]\d+",
        "dbGaP": r"phs\d+",
        "PubMed": r"(?<!\d)(\d{7,8})(?!\d)",
    }
    found: dict[str, list[str]] = {}
    for name, pat in patterns.items():
        hits = re.findall(pat, text, flags=re.I)
        # PubMed pattern returns groups; normalize
        if name == "PubMed":
            hits = [h if isinstance(h, str) else h for h in hits]
        uniq = sorted(set(hits), key=hits.index)
        if uniq:
            found[name] = uniq
    return found


def print_kv(label: str, value: str) -> None:
    if value and value != "N/A":
        print(f"  {label}: {value}")


def query_search(keywords: str, organism: str, entry: str, retmax: int) -> None:
    print(f"【GEO 检索】关键词：{keywords}")
    parts = [f"({keywords})", SC_HINT, f"{entry}[Entry Type]"]
    if organism:
        parts.append(f'"{organism}"[Organism]')
    term = " AND ".join(parts)
    ids, total = esearch("gds", term, retmax=retmax)
    records = esummary("gds", ids)
    if not records:
        print("  未找到结果。可去掉组织词重试，或换用英文关键词（liver / PBMC / spatial）。")
        return

    for i, rec in enumerate(records, 1):
        acc = rec.get("accession", "N/A")
        title = truncate(rec.get("title", "N/A"), 140)
        print(f"\n===== 结果 {i} =====")
        print(f"  登录号: {acc}")
        print(f"  标题: {title}")
        print_kv("物种", rec.get("taxon", "N/A"))
        print_kv("类型", rec.get("gdstype", "N/A"))
        print_kv("样本数", str(rec.get("n_samples", "N/A")))
        print_kv("平台 GPL", str(rec.get("gpl", "N/A")).replace(";", ", "))
        ftp = rec.get("ftplink") or ""
        if ftp:
            print(f"  FTP: {ftp}")
        print(f"  GEO: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={acc}")
        pubmed = rec.get("pubmedids") or []
        if pubmed:
            print(f"  PubMed: {', '.join(str(p) for p in pubmed)}")

    print(f"\n共检索到 {total} 条，展示前 {len(records)} 条（默认偏向单细胞/空间相关）。")
    print("提示：用 `gse GSE…` 看详情与补充矩阵；本 skill 不做聚类/注释分析。")


def query_gse(accession: str, sample_limit: int) -> None:
    acc = accession.upper().strip()
    if not acc.startswith("GSE"):
        raise ValueError("请提供 GSE 登录号，例如 GSE149614")
    print(f"【GEO Series】{acc}")
    fields = parse_soft(fetch_geo_soft(acc))
    title = first(fields, "Series_title")
    print(f"  标题: {title}")
    print_kv("状态", first(fields, "Series_status"))
    print_kv("提交", first(fields, "Series_submission_date"))
    print_kv("更新", first(fields, "Series_last_update_date"))
    print_kv("类型", "; ".join(all_vals(fields, "Series_type")) or "N/A")
    print_kv("物种", first(fields, "Series_sample_organism", "Series_platform_organism"))
    print_kv("平台", ", ".join(all_vals(fields, "Series_platform_id")) or "N/A")
    pubmed = all_vals(fields, "Series_pubmed_id")
    if pubmed:
        print(f"  PubMed: {', '.join(pubmed)}")
    web = all_vals(fields, "Series_web_link")
    if web:
        print(f"  网页: {', '.join(web)}")

    summary = first(fields, "Series_summary", default="")
    if summary:
        print(f"  摘要: {truncate(summary, 420)}")
    design = " ".join(all_vals(fields, "Series_overall_design"))
    if design.strip():
        print(f"  设计: {truncate(design, 420)}")

    samples = all_vals(fields, "Series_sample_id")
    print(f"  样本数: {len(samples)}")
    if samples:
        show = samples[:sample_limit]
        print(f"  样本示例: {', '.join(show)}" + (" …" if len(samples) > sample_limit else ""))

    relations = all_vals(fields, "Series_relation")
    if relations:
        print("  关联:")
        for rel in relations:
            print(f"    - {rel}")

    extracted = extract_accessions("\n".join(relations + [design, summary]))
    for key in ("BioProject", "SRA_Study", "EGA", "dbGaP"):
        if key in extracted:
            print(f"  {key}: {', '.join(extracted[key])}")

    suppl = all_vals(fields, "Series_supplementary_file")
    if suppl:
        print("  补充文件（常含表达矩阵，优先看这些）:")
        for path in suppl[:12]:
            name = path.rstrip("/").split("/")[-1] or path
            print(f"    - {unquote(name)}")
            print(f"      {path}")
        if len(suppl) > 12:
            print(f"    … 另有 {len(suppl) - 12} 个文件")
    else:
        print("  补充文件: 无（可能只有原始测序，见 SRA/EGA/dbGaP）")

    print(f"  GEO: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={acc}")
    # NCBI layout: GSE149614 → .../GSE149nnn/GSE149614/
    ftp = f"ftp://ftp.ncbi.nlm.nih.gov/geo/series/{acc[:-3]}nnn/{acc}/"
    print(f"  FTP: {ftp}")
    print("\n边界: 本命令只做检索与元数据；不运行 scanpy/Seurat。")


def query_gsm(accession: str) -> None:
    acc = accession.upper().strip()
    if not acc.startswith("GSM"):
        raise ValueError("请提供 GSM 登录号，例如 GSM4505964")
    print(f"【GEO Sample】{acc}")
    fields = parse_soft(fetch_geo_soft(acc, view="full"))
    print(f"  标题: {first(fields, 'Sample_title')}")
    print_kv("类型", first(fields, "Sample_type"))
    print_kv("状态", first(fields, "Sample_status"))
    print_kv("物种", first(fields, "Sample_organism_ch1"))
    print_kv("来源", first(fields, "Sample_source_name_ch1"))
    print_kv("平台", first(fields, "Sample_platform_id"))
    print_kv("仪器", first(fields, "Sample_instrument_model"))
    print_kv("文库策略", first(fields, "Sample_library_strategy"))
    print_kv("文库来源", first(fields, "Sample_library_source"))
    print_kv("分子", first(fields, "Sample_molecule_ch1"))
    series = all_vals(fields, "Sample_series_id")
    if series:
        print(f"  所属 Series: {', '.join(series)}")

    chars = all_vals(fields, "Sample_characteristics_ch1")
    if chars:
        print("  特征:")
        for c in chars[:20]:
            print(f"    - {c}")

    relations = all_vals(fields, "Sample_relation")
    if relations:
        print("  关联:")
        for rel in relations:
            print(f"    - {rel}")
    extracted = extract_accessions("\n".join(relations))
    for key in ("BioSample", "SRA_Experiment", "SRA_Run", "BioProject"):
        if key in extracted:
            print(f"  {key}: {', '.join(extracted[key])}")

    # Try BioSample -> SRA runinfo when SRR not embedded
    biosamples = extracted.get("BioSample") or []
    if biosamples and "SRA_Run" not in extracted:
        _try_print_sra_via_biosample(biosamples[0], limit=5)

    print(f"  GEO: https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc={acc}")


def _try_print_sra_via_biosample(biosample: str, limit: int = 5) -> None:
    ids, _ = esearch("biosample", biosample, retmax=1)
    if not ids:
        return
    sra_ids = elink_ids("biosample", "sra", ids[0])
    if not sra_ids:
        print("  SRA: 未通过 BioSample 链到公开 SRA（原始数据可能在 EGA/dbGaP 或仅有 GEO 矩阵）")
        return
    print(f"  关联 SRA 实验数(UID): {len(sra_ids)}（展示 runinfo 前 {min(limit, len(sra_ids))}）")
    _print_runinfo(sra_ids[:limit])


def _print_runinfo(sra_uids_or_empty: list[str] | None = None, accessions: list[str] | None = None) -> None:
    if accessions:
        # resolve accession -> uid then fetch
        uids: list[str] = []
        for acc in accessions:
            ids, _ = esearch("sra", acc, retmax=1)
            uids.extend(ids)
        sra_uids_or_empty = uids
    if not sra_uids_or_empty:
        print("  未找到 SRA Run")
        return
    text = _get_text(
        "efetch.fcgi",
        db="sra",
        id=",".join(sra_uids_or_empty),
        rettype="runinfo",
        retmode="text",
    )
    if not text.strip() or text.startswith("ID+list"):
        print("  runinfo 为空")
        return
    reader = csv.DictReader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        print("  runinfo 解析为空")
        return
    for i, row in enumerate(rows, 1):
        print(f"\n  --- Run {i} ---")
        for key in (
            "Run",
            "Experiment",
            "SRAStudy",
            "BioProject",
            "BioSample",
            "SampleName",
            "LibraryStrategy",
            "LibrarySource",
            "LibraryLayout",
            "Platform",
            "Model",
            "ScientificName",
            "spots",
            "bases",
            "size_MB",
            "Assay_Type",
        ):
            if key in row and row[key]:
                print(f"    {key}: {row[key]}")
        run = row.get("Run")
        if run:
            print(f"    页面: https://www.ncbi.nlm.nih.gov/sra/{run}")
            print(f"    下载: prefetch {run}  # 需安装 SRA Toolkit")


def query_bioproject(accession: str) -> None:
    acc = accession.upper().strip()
    if not re.match(r"^PRJ[NED][A-Z]\d+$", acc):
        raise ValueError("请提供 BioProject 登录号，例如 PRJNA629369")
    print(f"【BioProject】{acc}")
    ids, total = esearch("bioproject", acc, retmax=1)
    if not ids:
        print("  未找到 BioProject")
        return
    records = esummary("bioproject", ids)
    rec = records[0]
    print(f"  登录号: {rec.get('project_acc', acc)}")
    print(f"  标题: {rec.get('project_title') or rec.get('project_name') or 'N/A'}")
    print_kv("物种", rec.get("organism_name", "N/A"))
    print_kv("数据类型", rec.get("project_data_type", "N/A"))
    print_kv("提交机构", rec.get("submitter_organization", "N/A"))
    print_kv("注册日期", str(rec.get("registration_date", "N/A")))
    desc = rec.get("project_description") or ""
    if desc:
        print(f"  描述: {truncate(desc, 420)}")
    print(f"  页面: https://www.ncbi.nlm.nih.gov/bioproject/{acc}")

    # Linked GEO via elink
    geo_ids = elink_ids("bioproject", "gds", ids[0])
    if geo_ids:
        geo_recs = esummary("gds", geo_ids[:10])
        gses = [r.get("accession") for r in geo_recs if str(r.get("accession", "")).startswith("GSE")]
        if gses:
            print(f"  关联 GEO Series: {', '.join(gses)}")

    sra_ids = elink_ids("bioproject", "sra", ids[0])
    if sra_ids:
        print(f"  关联 SRA UID 数: {len(sra_ids)}")
        _print_runinfo(sra_ids[:5])
    else:
        # fallback accession field search
        sra_uids, sra_count = esearch("sra", f"{acc}[BioProject]", retmax=5)
        print(f"  SRA 检索命中: {sra_count}")
        if sra_uids:
            _print_runinfo(sra_uids)
        else:
            print("  提示: 无公开 SRA 链接时，请回 GEO 看补充矩阵，或查 EGA/dbGaP。")


def query_srr(accession: str) -> None:
    acc = accession.upper().strip()
    if not re.match(r"^(SRR|ERR|DRR)\d+$", acc):
        raise ValueError("请提供 Run 登录号，例如 SRR10000000")
    print(f"【SRA Run】{acc}")
    ids, total = esearch("sra", acc, retmax=1)
    if not ids:
        print("  未找到该 Run（可能未公开或登录号有误）")
        return
    print(f"  Entrez 命中: {total}")
    _print_runinfo(ids)


def query_sra_search(keywords: str, retmax: int) -> None:
    print(f"【SRA 检索】{keywords}")
    term = f"({keywords}) AND RNA-Seq[Strategy]"
    ids, total = esearch("sra", term, retmax=retmax)
    if not ids:
        print("  未找到结果")
        return
    print(f"  共检索到 {total} 条，展示 runinfo 前 {len(ids)} 条")
    _print_runinfo(ids)


def query_resolve(accession: str, sample_limit: int) -> None:
    acc = accession.upper().strip()
    print(f"【Resolve 链路】{acc}")
    if acc.startswith("GSE"):
        fields = parse_soft(fetch_geo_soft(acc))
        print(f"  Series: {acc} — {first(fields, 'Series_title')}")
        samples = all_vals(fields, "Series_sample_id")
        print(f"  GSM 数: {len(samples)}")
        relations = all_vals(fields, "Series_relation")
        extracted = extract_accessions(
            "\n".join(relations + all_vals(fields, "Series_overall_design", "Series_summary"))
        )
        bioprojects = extracted.get("BioProject") or []
        if bioprojects:
            print(f"  BioProject: {', '.join(bioprojects)}")
        else:
            print("  BioProject: 未在 Series_relation 中声明")

        suppl = all_vals(fields, "Series_supplementary_file")
        matrixish = [
            p
            for p in suppl
            if re.search(r"(count|umi|tpm|matrix|h5|h5ad|mtx|rds|csv|tsv|txt|raw)", p, re.I)
        ]
        print(f"  补充文件: {len(suppl)} 个；疑似矩阵/计数: {len(matrixish)} 个")
        for p in matrixish[:6]:
            print(f"    - {p}")

        if "EGA" in extracted:
            print(f"  受控原始数据(EGA): {', '.join(extracted['EGA'])}")
        if "dbGaP" in extracted:
            print(f"  受控原始数据(dbGaP): {', '.join(extracted['dbGaP'])}")

        if bioprojects:
            print("\n  → 展开 BioProject / SRA …")
            query_bioproject(bioprojects[0])
        elif samples:
            print(f"\n  → 抽样 GSM 解析 BioSample/SRA：{samples[0]}")
            query_gsm(samples[0])
        else:
            print("  无法继续解析")
        print("\n建议路径:")
        print("  1) 有矩阵补充文件 → 直接下载 GEO suppl 做分析")
        print("  2) 有公开 SRR → SRA Toolkit / AWS S3 拉 fastq")
        print("  3) 仅 EGA/dbGaP → 需申请访问，本 skill 只给出登录号")
        return

    if acc.startswith("GSM"):
        query_gsm(acc)
        return
    if acc.startswith("PRJ"):
        query_bioproject(acc)
        return
    if re.match(r"^(SRR|ERR|DRR)\d+$", acc):
        query_srr(acc)
        return
    raise ValueError("resolve 支持 GSE / GSM / PRJNA… / SRR…")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Query NCBI GEO / SRA / BioProject (discovery only, no scRNA analysis)"
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    p_search = sub.add_parser("search", help="Search GEO Series (scRNA/spatial-biased)")
    p_search.add_argument("keywords", help="e.g. 'liver' or 'PBMC COVID'")
    p_search.add_argument("--organism", default="Homo sapiens")
    p_search.add_argument("--entry", default="GSE", choices=["GSE", "GSM", "GPL"])
    p_search.add_argument("--limit", type=int, default=DISPLAY_LIMIT)

    p_gse = sub.add_parser("gse", help="GEO Series details")
    p_gse.add_argument("accession")
    p_gse.add_argument("--sample-limit", type=int, default=12)

    p_gsm = sub.add_parser("gsm", help="GEO Sample details")
    p_gsm.add_argument("accession")

    p_bp = sub.add_parser("bioproject", help="BioProject details")
    p_bp.add_argument("accession")

    p_srr = sub.add_parser("srr", help="SRA Run details")
    p_srr.add_argument("accession")

    p_sras = sub.add_parser("sra_search", help="Search SRA RNA-Seq runs")
    p_sras.add_argument("keywords")
    p_sras.add_argument("--limit", type=int, default=5)

    p_res = sub.add_parser("resolve", help="Resolve GSE→BioProject→SRA/download path")
    p_res.add_argument("accession")
    p_res.add_argument("--sample-limit", type=int, default=12)

    args = parser.parse_args()
    handlers = {
        "search": lambda: query_search(args.keywords, args.organism, args.entry, args.limit),
        "gse": lambda: query_gse(args.accession, args.sample_limit),
        "gsm": lambda: query_gsm(args.accession),
        "bioproject": lambda: query_bioproject(args.accession),
        "srr": lambda: query_srr(args.accession),
        "sra_search": lambda: query_sra_search(args.keywords, args.limit),
        "resolve": lambda: query_resolve(args.accession, args.sample_limit),
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
