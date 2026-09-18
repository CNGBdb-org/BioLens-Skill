"""Match atlas titles / PMIDs to publications.jsonl for DOI enrichment."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_title(text: str) -> str:
    return _NON_ALNUM.sub(" ", (text or "").lower()).strip()


def _title_tokens(text: str) -> set[str]:
    return {t for t in normalize_title(text).split() if len(t) > 2}


def title_similarity(a: str, b: str) -> float:
    """Jaccard similarity on word tokens."""
    ta, tb = _title_tokens(a), _title_tokens(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union if union else 0.0


def load_publications_index(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    by_pmid: dict[str, dict] = {}
    by_doi: dict[str, dict] = {}
    by_norm_title: dict[str, dict] = {}
    by_token: dict[str, list[dict]] = {}
    records: list[dict] = []

    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            records.append(rec)
            pmid = str(rec.get("pmid") or "").strip()
            doi = str(rec.get("doi") or "").strip()
            title = str(rec.get("title") or "").strip()
            if pmid:
                by_pmid[pmid] = rec
            if doi:
                by_doi[doi.lower()] = rec
            norm = normalize_title(title)
            if norm and norm not in by_norm_title:
                by_norm_title[norm] = rec
            for tok in _title_tokens(title):
                by_token.setdefault(tok, []).append(rec)

    return {
        "records": records,
        "by_pmid": by_pmid,
        "by_doi": by_doi,
        "by_norm_title": by_norm_title,
        "by_token": by_token,
    }


@lru_cache(maxsize=1)
def default_publications_index() -> dict[str, Any]:
    datasets_root = Path(__file__).resolve().parents[3]  # .../datasets
    repo_root = datasets_root.parents[2]  # .../stomics_cdcp
    path = repo_root / "web" / "data" / "publications.jsonl"
    if path.is_file():
        return load_publications_index(path)
    return {"records": [], "by_pmid": {}, "by_doi": {}, "by_norm_title": {}}


def lookup_doi_by_pmid(pmid: str, index: dict[str, Any] | None = None) -> str:
    pmid = str(pmid or "").strip()
    if not pmid:
        return ""
    idx = index or default_publications_index()
    rec = idx["by_pmid"].get(pmid)
    return str(rec.get("doi") or "").strip() if rec else ""


def match_publication_by_title(
    title: str,
    index: dict[str, Any] | None = None,
    *,
    min_score: float = 0.72,
) -> dict | None:
    title = (title or "").strip()
    if len(title) < 12:
        return None
    idx = index or default_publications_index()
    norm = normalize_title(title)
    if norm in idx["by_norm_title"]:
        return idx["by_norm_title"][norm]

    best: dict | None = None
    best_score = 0.0
    candidates: dict[int, dict] = {}
    tokens = sorted(_title_tokens(title), key=len, reverse=True)
    if tokens and idx.get("by_token"):
        for tok in tokens[:6]:
            for rec in idx["by_token"].get(tok, []):
                candidates[id(rec)] = rec
    pool = candidates.values() if candidates else idx["records"]
    for rec in pool:
        pub_title = str(rec.get("title") or "")
        score = title_similarity(title, pub_title)
        if score > best_score:
            best_score = score
            best = rec
    if best_score >= min_score:
        return best
    return None


def enrich_literature_entry(
    entry: dict[str, str],
    *,
    index: dict[str, Any] | None = None,
    title: str = "",
) -> dict[str, str]:
    """Fill missing doi/citation/pmid on an atlas literature cache entry."""
    out = dict(entry)
    idx = index or default_publications_index()

    if out.get("pmid") and not out.get("doi"):
        doi = lookup_doi_by_pmid(out["pmid"], idx)
        if doi:
            out["doi"] = doi

    if not out.get("doi") and title:
        rec = match_publication_by_title(title, idx)
        if rec:
            if not out.get("doi") and rec.get("doi"):
                out["doi"] = str(rec["doi"])
            if not out.get("pmid") and rec.get("pmid"):
                out["pmid"] = str(rec["pmid"])
            if not out.get("citation") and rec.get("title"):
                authors = str(rec.get("authors") or "").split("|")[0].strip()
                journal = str(rec.get("journal") or "").strip()
                cite = rec["title"]
                if authors:
                    cite = f"{authors}. {cite}"
                if journal:
                    cite = f"{cite} {journal}"
                if out.get("doi"):
                    cite = f"{cite} doi:{out['doi']}"
                out["citation"] = cite[:500]

    return out
