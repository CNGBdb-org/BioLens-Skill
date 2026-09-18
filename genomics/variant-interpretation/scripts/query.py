#!/usr/bin/env python3
"""Orchestrate dbsnp → gnomad → clinvar for variant triage."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

_LIB = Path(__file__).resolve().parent / "_lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))

from peer_skills import find_skill_dir  # noqa: E402
from result import emit_json, envelope  # noqa: E402

_HERE = Path(__file__).resolve()
STEP_DELAY = 0.35  # polite pause between NCBI-heavy steps


def _run_skill(skill: str, args: list[str], *, timeout: int = 180) -> dict[str, Any]:
    skill_dir = find_skill_dir(skill, _HERE)
    script = (skill_dir / "scripts" / "query.py") if skill_dir else None
    if script is None or not script.is_file():
        return {
            "ok": False,
            "source": skill,
            "mode": "missing",
            "schema": "cngbdb.skill-result.v2",
            "message": f"Skill script not found: {skill}",
        }
    cmd = [sys.executable, str(script), *args, "--format", "json"]
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(script.parent.parent),
        )
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "source": skill,
            "mode": "timeout",
            "schema": "cngbdb.skill-result.v2",
            "message": f"{skill} timed out",
        }
    raw = (proc.stdout or "").strip()
    if not raw:
        err = (proc.stderr or "").strip() or f"exit {proc.returncode}"
        return {
            "ok": False,
            "source": skill,
            "mode": "empty",
            "schema": "cngbdb.skill-result.v2",
            "message": err[:500],
        }
    # Prefer last JSON object if any logs leaked
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start : end + 1])
            except json.JSONDecodeError:
                pass
        return {
            "ok": False,
            "source": skill,
            "mode": "parse_error",
            "schema": "cngbdb.skill-result.v2",
            "message": raw[:500],
        }


def normalize_rsid(rsid: str) -> str:
    rsid = rsid.strip().replace("RS", "rs").replace("Rs", "rs")
    if not rsid.lower().startswith("rs"):
        rsid = f"rs{rsid}"
    return rsid if rsid.startswith("rs") else f"rs{rsid}"


def _pick_rsid_from_dbsnp(payload: dict[str, Any]) -> str | None:
    if not payload:
        return None
    if payload.get("label") and re.match(r"^rs\d+$", str(payload["label"]), re.I):
        return normalize_rsid(str(payload["label"]))
    extra = payload.get("rsids") or []
    if isinstance(extra, list) and extra:
        return normalize_rsid(str(extra[0]))
    rec = payload.get("record") or {}
    if isinstance(rec, dict) and rec.get("rsID"):
        return normalize_rsid(str(rec["rsID"]))
    for item in payload.get("records") or []:
        if isinstance(item, dict) and item.get("rsID"):
            return normalize_rsid(str(item["rsID"]))
    return None


def _first_value(obj: dict[str, Any] | None, *keys: str) -> Any:
    if not isinstance(obj, dict):
        return None
    for k in keys:
        if obj.get(k) not in (None, "", []):
            return obj[k]
    return None


def _summarize(steps: dict[str, Any], rsid: str | None) -> dict[str, Any]:
    dbsnp = steps.get("dbsnp") or {}
    gnomad = steps.get("gnomad") or {}
    clinvar = steps.get("clinvar") or {}

    af_note = None
    g_rec = gnomad.get("record") if isinstance(gnomad.get("record"), dict) else None
    if g_rec:
        af_note = _first_value(
            g_rec,
            "af_interpretation",
            "interpretation",
            "AF解读",
            "AF",
            "allele_frequency",
        )
        if af_note is not None and not isinstance(af_note, str):
            af_note = f"AF={af_note}"
    elif gnomad.get("ok") is False:
        af_note = gnomad.get("message") or "gnomAD 未命中"
    elif gnomad.get("mode") == "skipped":
        af_note = "skipped"

    clin_note = None
    c_rec = clinvar.get("record") if isinstance(clinvar.get("record"), dict) else None
    if c_rec:
        clin_note = _first_value(c_rec, "clinical_significance", "significance", "临床意义")
    elif clinvar.get("records"):
        first = clinvar["records"][0]
        if isinstance(first, dict):
            clin_note = _first_value(first, "clinical_significance", "significance", "临床意义")
    elif clinvar.get("ok") is False:
        clin_note = clinvar.get("message") or "ClinVar 未命中"
    elif clinvar.get("mode") == "skipped":
        clin_note = "skipped"

    loc = None
    d_rec = dbsnp.get("record") if isinstance(dbsnp.get("record"), dict) else None
    if d_rec:
        loc = _first_value(d_rec, "chrpos", "位置(GRCh38)", "位置(GRCh37)", "chromosome", "染色体")

    return {
        "rsid": rsid,
        "location": loc,
        "population_af": af_note,
        "clinical_significance": clin_note,
        "pipeline": ["dbsnp", "gnomad", "clinvar"],
        "partial": any(
            (steps.get(s) or {}).get("ok") is False for s in ("dbsnp", "gnomad", "clinvar")
        ),
        "disclaimer": (
            "编排结果仅供科研参考，不构成临床诊断；"
            "ACMG/AMP 终判需结合表型与实验室规范。"
        ),
    }


def interpret(
    *,
    rsid: str | None = None,
    hgvs: str | None = None,
    chrom: str | None = None,
    pos: str | None = None,
    assembly: str = "GRCh38",
    dataset: str = "gnomad_r4",
    skip_gnomad: bool = False,
    skip_clinvar: bool = False,
) -> dict[str, Any]:
    steps: dict[str, Any] = {}
    resolved: str | None = None

    if rsid:
        resolved = normalize_rsid(rsid)
        steps["dbsnp"] = _run_skill("dbsnp", ["rsid", resolved])
    elif hgvs:
        steps["dbsnp"] = _run_skill("dbsnp", ["hgvs", hgvs])
        resolved = _pick_rsid_from_dbsnp(steps["dbsnp"])
    elif chrom and pos:
        steps["dbsnp"] = _run_skill("dbsnp", ["coord", chrom, pos, "--assembly", assembly])
        resolved = _pick_rsid_from_dbsnp(steps["dbsnp"])
    else:
        return envelope(
            source="variant-interpretation",
            mode="interpret",
            ok=False,
            message="需要 --rsid、--hgvs 或 --chrom/--pos 之一",
        )

    if not resolved:
        summary = _summarize(steps, None)
        return envelope(
            source="variant-interpretation",
            mode="interpret",
            ok=False,
            label=rsid or hgvs or f"{chrom}:{pos}",
            message="未能解析到 rsID，已停止 gnomAD/ClinVar 步骤",
            record={"steps": steps, "summary": summary},
        )

    time.sleep(STEP_DELAY)
    if not skip_gnomad:
        steps["gnomad"] = _run_skill(
            "gnomad", ["rsid", resolved, "--dataset", dataset], timeout=240,
        )
        time.sleep(STEP_DELAY)
    else:
        steps["gnomad"] = {
            "ok": True,
            "source": "gnomad",
            "mode": "skipped",
            "schema": "cngbdb.skill-result.v2",
            "message": "skipped",
        }

    if not skip_clinvar:
        steps["clinvar"] = _run_skill("clinvar", ["rsid", resolved], timeout=120)
    else:
        steps["clinvar"] = {
            "ok": True,
            "source": "clinvar",
            "mode": "skipped",
            "schema": "cngbdb.skill-result.v2",
            "message": "skipped",
        }

    summary = _summarize(steps, resolved)
    ok = bool((steps.get("dbsnp") or {}).get("ok", True)) or bool(resolved)
    # Overall ok if we at least resolved rsID; partial failures stay in summary
    return envelope(
        source="variant-interpretation",
        mode="interpret",
        ok=ok,
        label=resolved,
        record={"steps": steps, "summary": summary},
        extra={"dataset": dataset, "assembly": assembly},
    )


def _print_text(result: dict[str, Any]) -> None:
    summary = (result.get("record") or {}).get("summary") or {}
    steps = (result.get("record") or {}).get("steps") or {}
    print("【变异综合解读】dbsnp → gnomad → clinvar")
    print(f"  rsID: {summary.get('rsid') or result.get('label') or 'N/A'}")
    if summary.get("location"):
        print(f"  位置: {summary['location']}")
    print(f"  人群频率: {summary.get('population_af') or 'N/A'}")
    print(f"  临床意义: {summary.get('clinical_significance') or 'N/A'}")
    if summary.get("partial"):
        print("  注意: 部分步骤失败或未命中（见下方 steps）")
    print(f"  声明: {summary.get('disclaimer', '')}")
    print()
    for name in ("dbsnp", "gnomad", "clinvar"):
        step = steps.get(name) or {}
        status = "ok" if step.get("ok", True) and step.get("mode") != "skipped" else (
            "skipped" if step.get("mode") == "skipped" else "fail"
        )
        msg = step.get("message") or step.get("label") or ""
        print(f"  [{name}] {status}" + (f" — {msg}" if msg else ""))
    if not result.get("ok"):
        print(f"\n失败: {result.get('message')}", file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser(
        description="Cross-DB variant interpretation: dbsnp → gnomad → clinvar",
    )
    p.add_argument("--rsid", help="rsID, e.g. rs80357906")
    p.add_argument("--hgvs", help="HGVS to resolve via dbSNP first")
    p.add_argument("--chrom", help="Chromosome for coordinate resolve")
    p.add_argument("--pos", help="Position for coordinate resolve")
    p.add_argument("--assembly", default="GRCh38", choices=["GRCh38", "GRCh37"])
    p.add_argument("--dataset", default="gnomad_r4", help="gnomAD dataset id")
    p.add_argument("--skip-gnomad", action="store_true")
    p.add_argument("--skip-clinvar", action="store_true")
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    n_inputs = sum(bool(x) for x in (args.rsid, args.hgvs, args.chrom))
    if n_inputs != 1:
        p.error("Specify exactly one of --rsid, --hgvs, or --chrom/--pos")
    if args.chrom and not args.pos:
        p.error("--chrom requires --pos")

    try:
        result = interpret(
            rsid=args.rsid,
            hgvs=args.hgvs,
            chrom=args.chrom,
            pos=args.pos,
            assembly=args.assembly,
            dataset=args.dataset,
            skip_gnomad=args.skip_gnomad,
            skip_clinvar=args.skip_clinvar,
        )
    except Exception as exc:  # noqa: BLE001 — surface as envelope
        result = envelope(
            source="variant-interpretation",
            mode="interpret",
            ok=False,
            message=str(exc),
        )

    if args.format == "json":
        emit_json(result)
    else:
        _print_text(result)
    if not result.get("ok"):
        sys.exit(1)


if __name__ == "__main__":
    main()
