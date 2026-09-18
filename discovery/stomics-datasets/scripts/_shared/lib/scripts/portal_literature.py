"""Fetch atlas-level DOI/PMID/citation from CNGB STOmics / CDCP portal APIs."""

from __future__ import annotations

import json
import re
import ssl
import urllib.error
import urllib.request
from functools import lru_cache
from typing import Any

import certifi

SSL = ssl.create_default_context(cafile=certifi.where())
UA = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

STDS_PORTAL = "https://db.cngb.org/stomics/datasets/{stds_id}/"
CDCP_API = "https://db.cngb.org/cdcp/api/datasets/{scds_id}"

_DOI_RE = re.compile(
    r"(?:doi:\s*|https?://(?:dx\.)?doi\.org/)(10\.\d{4,9}/[^\s\"'<>]+)",
    re.I,
)


def parse_doi_from_text(text: str) -> str:
    if not text:
        return ""
    m = _DOI_RE.search(text)
    if m:
        return m.group(1).rstrip(".,;)")
    return ""


def parse_pmid(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (int, float)):
        return str(int(value))
    if isinstance(value, str) and value.strip().isdigit():
        return value.strip()
    if isinstance(value, list) and value:
        first = value[0]
        if isinstance(first, dict):
            return str(first.get("pmid") or "").strip()
        return parse_pmid(first)
    if isinstance(value, dict):
        return str(value.get("pmid") or "").strip()
    return ""


def _fetch_stds_state(stds_id: str) -> dict | None:
    url = STDS_PORTAL.format(stds_id=stds_id.upper())
    req = urllib.request.Request(url, headers=UA)
    try:
        html = urllib.request.urlopen(req, context=SSL, timeout=30).read().decode(
            errors="replace"
        )
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError):
        return None
    marker = "__INITIAL_STATE__="
    if marker not in html:
        return None
    start = html.index(marker) + len(marker)
    end = html.index("</script>", start)
    try:
        return json.loads(html[start:end].strip().rstrip(";"))
    except json.JSONDecodeError:
        return None


def _fetch_cdcp_data(scds_id: str) -> dict | None:
    url = CDCP_API.format(scds_id=scds_id.upper())
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, context=SSL, timeout=30) as resp:
            body = json.loads(resp.read())
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError):
        return None
    data = body.get("data") if isinstance(body, dict) else None
    return data if isinstance(data, dict) else None


def literature_from_portal_data(data: dict) -> dict[str, str]:
    citation = (data.get("citation") or "").strip()
    doi = (data.get("data_doi") or "").strip() or parse_doi_from_text(citation)
    pmid = parse_pmid(data.get("pmids")) or parse_pmid(data.get("pmid"))
    title = (data.get("title") or "").strip()
    portal = ""
    ds_id = (data.get("dataset_id") or data.get("id") or "").strip()
    if ds_id.upper().startswith("STDS"):
        portal = f"https://db.cngb.org/stomics/datasets/{ds_id.upper()}/"
    elif ds_id.upper().startswith("SCDS"):
        portal = f"https://db.cngb.org/cdcp/dataset/{ds_id.upper()}"
    return {
        "doi": doi,
        "pmid": pmid,
        "citation": citation[:500],
        "dataset_title": title[:300],
        "portal_url": portal,
    }


def fetch_atlas_literature(atlas_id: str) -> dict[str, str]:
    """Return doi/pmid/citation for a portal atlas id (STDS* / SCDS* / named via registry)."""
    aid = (atlas_id or "").strip()
    if not aid:
        return {}
    upper = aid.upper()
    if upper.startswith("STDS"):
        state = _fetch_stds_state(upper)
        if not state:
            return {}
        data = state.get("Dataset", {}).get("data", {}) or {}
        out = literature_from_portal_data(data)
        if not out.get("portal_url"):
            out["portal_url"] = STDS_PORTAL.format(stds_id=upper)
        return out
    if upper.startswith("SCDS"):
        data = _fetch_cdcp_data(upper)
        if not data:
            return {}
        out = literature_from_portal_data(data)
        if not out.get("portal_url"):
            out["portal_url"] = f"https://db.cngb.org/cdcp/dataset/{upper}"
        return out
    return {}


def _species_label(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        if not value:
            return ""
        first = value[0]
        if isinstance(first, dict):
            names = first.get("common_names") or []
            if names:
                return str(names[0]).strip()
            return str(first.get("scientific_name") or "").strip()
        return str(first).strip()
    if isinstance(value, dict):
        names = value.get("common_names") or []
        if names:
            return str(names[0]).strip()
        return str(value.get("scientific_name") or value.get("name") or "").strip()
    return str(value).strip()


def _join_field(value: Any, *, limit: int = 8) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        parts = [str(v).strip() for v in value if str(v).strip()]
        if len(parts) > limit:
            return ", ".join(parts[:limit]) + f" 等 {len(parts)} 项"
        return ", ".join(parts)
    return str(value).strip()


def portal_record_from_data(data: dict, *, atlas_id: str = "") -> dict[str, str]:
    """Normalize STDS/SCDS portal payload for intro distillation."""
    ds_id = (data.get("dataset_id") or data.get("id") or atlas_id or "").strip().upper()
    portal_url = ""
    if ds_id.startswith("STDS"):
        portal_url = STDS_PORTAL.format(stds_id=ds_id)
    elif ds_id.startswith("SCDS"):
        portal_url = f"https://db.cngb.org/cdcp/dataset/{ds_id}"

    tech = (
        data.get("stomics_technologies")
        or data.get("technology")
        or data.get("platforms")
        or ""
    )
    tissues = data.get("tissues") or data.get("organ_parts") or ""
    sample_n = data.get("sample_number") or data.get("samples") or data.get("section_number") or ""
    if isinstance(sample_n, list):
        sample_n = len(sample_n)

    return {
        "atlas_id": ds_id,
        "title": str(data.get("title") or "").strip(),
        "summary": str(data.get("summary") or data.get("overall_design") or "").strip(),
        "citation": str(data.get("citation") or "").strip(),
        "species": _species_label(data.get("species")),
        "tissues": _join_field(tissues, limit=6),
        "technology": _join_field(tech, limit=4),
        "sample_number": str(sample_n).strip() if sample_n not in (None, "") else "",
        "portal_url": portal_url,
    }


def fetch_portal_dataset_record(atlas_id: str) -> dict[str, str] | None:
    """Fetch normalized portal fields (title/summary/species/…) for STDS/SCDS."""
    aid = (atlas_id or "").strip().upper()
    if not aid:
        return None
    if aid.startswith("STDS"):
        state = _fetch_stds_state(aid)
        if not state:
            return None
        data = state.get("Dataset", {}).get("data", {}) or {}
        if not data:
            return None
        return portal_record_from_data(data, atlas_id=aid)
    if aid.startswith("SCDS"):
        data = _fetch_cdcp_data(aid)
        if not data:
            return None
        return portal_record_from_data(data, atlas_id=aid)
    return None


@lru_cache(maxsize=2048)
def cached_atlas_literature(atlas_id: str) -> dict[str, str]:
    return fetch_atlas_literature(atlas_id)
