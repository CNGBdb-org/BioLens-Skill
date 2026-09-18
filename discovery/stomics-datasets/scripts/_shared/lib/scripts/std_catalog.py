"""Generic dataset catalog for STOmics atlases (reads datasets_list.tsv by Atlas)."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from atlas_registry import get_atlas
from catalog_io import CATALOG_BASENAME, find_catalog_path as _find_catalog_path, iter_catalog_rows


@dataclass(frozen=True)
class AtlasEntry:
    section: str
    stage_label: str = ""
    kind_label: str = ""
    tissue: str = ""
    download: str = ""
    technology: str = ""
    explore_id: str = ""
    n_obs: str = ""
    n_genes: str = ""

    @property
    def h5ad(self):
        return self.section if self.section.endswith(".h5ad") else f"{self.section}.h5ad"

    @property
    def stem(self):
        name = self.section
        return name[:-5] if name.endswith(".h5ad") else name

    @property
    def dataset_id(self):
        return f"{get_atlas().api_prefix}{self.stem}"

    @property
    def tissues(self):
        return [t.strip() for t in self.tissue.split(",") if t.strip()]

    @property
    def stage(self):
        return self.stage_label or self.stem

    @property
    def kind(self):
        return self.kind_label or "other"


def find_catalog_path():
    spec = get_atlas()
    return _find_catalog_path(legacy_basename=f"{spec.name}_list.tsv")


def load_catalog(path=None):
    spec = get_atlas()
    path = path or find_catalog_path()
    if not path:
        raise FileNotFoundError(
            f"{CATALOG_BASENAME} or {spec.name}_list.tsv not found "
            f"(or set STOMICS_CATALOG / {spec.name.upper()}_LIST)."
        )
    merged = os.path.basename(path) == CATALOG_BASENAME or path.endswith(os.sep + CATALOG_BASENAME)
    entries = []
    atlas_key = (spec.catalog_atlas or spec.name).lower()
    for row in iter_catalog_rows(path, atlas=spec.catalog_atlas or spec.name if merged else None):
        if merged and (row.get("Atlas") or "").strip().lower() != atlas_key:
            continue
        section = (row.get("Section") or "").strip()
        if not section:
            continue
        entries.append(
            AtlasEntry(
                section=section,
                stage_label=(row.get("Developmental stage") or "").strip(),
                kind_label=(row.get("Kind") or "").strip(),
                tissue=(row.get("Tissue") or "").strip(),
                download=(row.get("Download") or "").strip(),
                technology=(row.get("Technology") or "").strip(),
                explore_id=(row.get("ExploreId") or "").strip(),
                n_obs=(row.get("n_obs") or "").strip(),
                n_genes=(row.get("n_genes") or "").strip(),
            )
        )
    return entries


def _norm(s):
    return s.strip().lower().replace(" ", "_")


def resolve_dataset_ref(query):
    query = str(query).strip().rstrip("/")
    if not query:
        raise ValueError("Empty dataset query")

    prefix = get_atlas().api_prefix
    if prefix and query.startswith(prefix):
        dataset_id = query
        try:
            catalog = load_catalog()
        except FileNotFoundError:
            catalog = []
        stem = dataset_id[len(prefix) :]
        entry = next((e for e in catalog if e.stem == stem or e.dataset_id == dataset_id), None)
        return dataset_id, entry

    catalog = load_catalog()
    q_lower = query.lower()
    q_norm = _norm(query)

    if query.endswith(".h5ad"):
        for e in catalog:
            if e.section.lower() == q_lower or e.h5ad.lower() == q_lower:
                return e.dataset_id, e
    else:
        for e in catalog:
            if e.stem.lower() == q_lower or e.section.lower() == q_lower:
                return e.dataset_id, e

    matches = []
    for e in catalog:
        hay = " ".join([e.section, e.stem, e.stage, e.kind, e.dataset_id]).lower()
        if q_lower in hay or q_norm in _norm(hay):
            matches.append(e)

    if len(matches) == 1:
        e = matches[0]
        return e.dataset_id, e
    if len(matches) > 1:
        lines = [f"  {e.dataset_id}  ({e.kind}, {e.section})" for e in matches[:15]]
        more = f"\n  ... and {len(matches) - 15} more" if len(matches) > 15 else ""
        raise ValueError(
            f"Ambiguous dataset '{query}' — {len(matches)} matches. Be more specific, e.g.:\n"
            + "\n".join(lines)
            + more
        )

    if not prefix:
        raise ValueError(f"No API prefix for atlas; cannot resolve '{query}' (FTP-only atlas).")
    stem = query[:-5] if query.endswith(".h5ad") else query
    return f"{prefix}{stem}", None


def search_catalog(*, stage=None, kind=None, tissue=None, technology=None, sex=None, text=None):
    catalog = load_catalog()
    out = catalog
    if stage:
        s = stage.lower()
        out = [e for e in out if s in e.stage.lower() or s in e.stem.lower()]
    if kind:
        k = kind.lower()
        out = [e for e in out if e.kind == k]
    if tissue:
        t = tissue.lower()
        out = [e for e in out if any(t in x.lower() for x in e.tissues)]
    if technology:
        tech = technology.lower()
        out = [e for e in out if tech in e.technology.lower()]
    if sex:
        sx = sex.lower()
        out = [e for e in out if sx in (getattr(e, "sex", "") or "").lower()]
    if text:
        q = text.lower()
        out = [
            e
            for e in out
            if q in e.section.lower()
            or q in e.stem.lower()
            or q in e.stage.lower()
            or q in e.kind.lower()
            or q in e.dataset_id.lower()
        ]
    return out


def is_sagittal_section(entry):
    return "sagittal" in entry.kind.lower()


def is_parquet_section(entry):
    if entry.kind.lower() in ("cirro_portal", "portal_spa"):
        return False
    if entry.explore_id:
        return True
    if entry.kind == "ftp_only":
        return False
    spec = get_atlas()
    if not spec.api_prefix:
        return False
    k = entry.kind.lower()
    if k in ("ftp_only", "h5ad", "scrna_h5ad"):
        return False
    if k in ("scrna", "snrna", "reference", "other"):
        return False
    if "spatial" in k or "coronal" in k or "sagittal" in k or "spc" in k or "stereoseq" in k:
        return True
    if entry.section.lower().endswith(".h5ad"):
        return True
    return True


def slice_sort_key(entry):
    import re

    m = re.search(r"T(\d+)", entry.stem, re.I)
    if m:
        return (0, int(m.group(1)), entry.stem)
    return (1, 0, entry.stem)


def stage_sort_key(stage):
    return slice_sort_key(type("E", (), {"stem": stage or ""})())


def score_entry(entry, *, tissue=None, prefer_sagittal=True):
    if tissue:
        t = tissue.lower()
        if entry.tissues and not any(t in x.lower() for x in entry.tissues):
            return None
    if not is_parquet_section(entry):
        return None
    score = len(entry.tissues) + 10
    if tissue and entry.tissues:
        score += 20
    if prefer_sagittal and is_sagittal_section(entry):
        score += 30
    score += slice_sort_key(entry) / 10000.0
    return score
