"""Resolve CNGB Cirrocumulus explore dataset ids from catalog rows / entries."""

from __future__ import annotations

import gzip
import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Callable

import certifi

EXPLORE_FILE_API = "https://db.cngb.org/stomics/api/explore/api/file"

_SCDS_ID_RE = re.compile(r"^SCDS\d{7}$", re.I)
_STDS_ID_RE = re.compile(r"^STDS\d{7}$", re.I)
_CDCP_PATH_RE = re.compile(r"/cdcp/(SCDS\d{7})/", re.I)
_DATASET_ID_SCDS = re.compile(r"^(SCDS\d{7})_", re.I)
_INVALID_EXPLORE = re.compile(r"^SCDS\d{7}_.*_processed$", re.I)

_SSL = ssl.create_default_context(cafile=certifi.where())
_UA = {"User-Agent": "Mozilla/5.0"}


def explore_stem_from_section(section: str) -> str:
    stem = section[:-5] if section.lower().endswith(".h5ad") else section
    if stem.endswith("_processed"):
        stem = stem[: -len("_processed")]
    return stem.strip()


def _is_invalid_explore_id(eid: str) -> bool:
    """dataset_id mistaken for explore id."""
    return bool(_INVALID_EXPLORE.match(eid))


def probe_explore_id(explore_id: str, *, timeout: float = 12.0) -> bool:
    """True if explore API serves index.json.gz for this dataset id."""
    eid = (explore_id or "").strip()
    if not eid:
        return False
    q = urllib.parse.urlencode({"id": eid, "file": "index.json.gz"})
    url = f"{EXPLORE_FILE_API}?{q}"
    try:
        req = urllib.request.Request(url, method="GET", headers=_UA)
        with urllib.request.urlopen(req, context=_SSL, timeout=timeout) as resp:
            raw = resp.read()
        if not raw:
            return False
        try:
            json.loads(gzip.decompress(raw))
        except gzip.BadGzipFile:
            json.loads(raw)
        return True
    except (urllib.error.HTTPError, urllib.error.URLError, OSError, TimeoutError, json.JSONDecodeError):
        return False


def load_stds_explore_map(probe_report_path: str) -> dict[tuple[str, str], str]:
    """(stds_id_lower, section_lower) -> verified STDS explore id from probe report."""
    try:
        with open(probe_report_path, encoding="utf-8") as f:
            report = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[tuple[str, str], str] = {}
    for item in report:
        stds_id = (item.get("stds_id") or "").strip()
        if not stds_id:
            continue
        for ent in item.get("h5ad_entries") or item.get("spatial_h5ad") or []:
            if not ent.get("shape"):
                continue
            fn = (ent.get("filename") or "").strip()
            stem = (ent.get("stem") or explore_stem_from_section(fn)).strip()
            if not fn or not stem:
                continue
            eid = f"{stds_id}_{stem}"
            out[(stds_id.lower(), fn.lower())] = eid
            out[(stds_id.lower(), stem.lower())] = eid
    return out


def load_cdcp_explore_map(probe_report_path: str) -> dict[tuple[str, str], str]:
    """(scds_id_lower, section_lower) -> explore_id from cdcp probe report."""
    try:
        with open(probe_report_path, encoding="utf-8") as f:
            report = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[tuple[str, str], str] = {}
    if not isinstance(report, dict):
        return out
    for scds_id, probe in report.items():
        if not isinstance(probe, dict):
            continue
        for ent in probe.get("h5ad_entries") or probe.get("entries") or []:
            eid = (ent.get("explore_id") or "").strip()
            if not eid:
                continue
            fn = (ent.get("filename") or "").strip()
            if fn:
                out[(scds_id.lower(), fn.lower())] = eid
            stem = (ent.get("stem") or explore_stem_from_section(fn)).strip()
            if stem:
                out[(scds_id.lower(), stem.lower())] = eid
    return out


def infer_explore_id_for_catalog_row(
    row: dict,
    *,
    stds_map: dict[tuple[str, str], str] | None = None,
    cdcp_map: dict[tuple[str, str], str] | None = None,
    lookup_atlas: Callable[[str], object | None] | None = None,
) -> str:
    """Infer explore id from catalog row (before API verification)."""
    existing = (row.get("ExploreId") or row.get("explore_id") or "").strip()
    if existing and not _is_invalid_explore_id(existing):
        if existing.startswith("cdcp_") or existing.startswith("embryodev_"):
            return existing
        if existing.startswith("STDS") and "_processed" not in existing:
            return existing
        if not _SCDS_ID_RE.match(existing.split("_", 1)[0] if "_" in existing else ""):
            return existing

    atlas = (row.get("Atlas") or "").strip()
    section = (row.get("Section") or "").strip()
    if not atlas or not section:
        return ""

    sec_key = section.lower()
    stem = explore_stem_from_section(section)
    kind = (row.get("Kind") or "").lower()
    download = (row.get("Download") or "").strip()

    if atlas.lower() == "mccsta" and kind not in ("coronal_bin200", "sagittal_bin200", "spatial"):
        return ""

    stds_map = stds_map or {}
    cdcp_map = cdcp_map or {}

    if _STDS_ID_RE.match(atlas):
        eid = stds_map.get((atlas.lower(), sec_key)) or stds_map.get((atlas.lower(), stem.lower()))
        if eid:
            return eid
        return f"{atlas.upper()}_{stem}" if stem else ""

    scds_key = atlas.lower()
    m = _CDCP_PATH_RE.search(download)
    scds = m.group(1).upper() if m else (atlas.upper() if _SCDS_ID_RE.match(atlas) else "")
    if scds:
        eid = cdcp_map.get((scds.lower(), sec_key)) or cdcp_map.get((scds.lower(), stem.lower()))
        if eid:
            return eid
        return f"cdcp_{scds}_{stem}" if stem else ""

    if lookup_atlas:
        spec = lookup_atlas(atlas)
        if spec and stem:
            prefix = getattr(spec, "api_prefix", "") or ""
            if prefix:
                return f"{prefix}{stem}"

    return ""


def resolve_cdcp_explore_id(row: dict) -> str:
    """CDCP portal rows use cdcp_SCDS… explore ids (runtime fallback)."""
    explore = (row.get("ExploreId") or row.get("explore_id") or "").strip()
    if explore.startswith("cdcp_"):
        return explore
    if explore and not _is_invalid_explore_id(explore):
        return explore
    return infer_explore_id_for_catalog_row(row)


def resolve_catalog_entry_explore_id(entry, *, api_prefix: str = "") -> str:
    """AtlasEntry → explore id; prefer catalog ExploreId column."""
    raw = (getattr(entry, "explore_id", None) or "").strip()
    if raw and not _is_invalid_explore_id(raw):
        return raw
    row = {
        "Section": getattr(entry, "section", "") or "",
        "Download": getattr(entry, "download", "") or "",
        "Kind": getattr(entry, "kind_label", "") or getattr(entry, "kind", "") or "",
    }
    if api_prefix:
        m = _DATASET_ID_SCDS.match(api_prefix)
        if m:
            row["Atlas"] = m.group(1).upper()
    return infer_explore_id_for_catalog_row(row)


def resolve_sample_explore_id(row: dict) -> str:
    """Explore id from list_datasets JSON — use catalog ExploreId column."""
    eid = (row.get("explore_id") or row.get("ExploreId") or "").strip()
    if eid and not _is_invalid_explore_id(eid):
        return eid
    return ""
