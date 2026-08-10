"""CIMA dataset catalog (6 lineage views from scripts/catalog.tsv)."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass

SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)
from catalog_io import CATALOG_BASENAME, find_catalog_path as _find_catalog_path, iter_catalog_rows


@dataclass(frozen=True)
class CimaEntry:
    section: str
    sex: str
    stage: str
    technology: str
    tissue: str
    spatial_clustering: str
    he: str
    download: str
    explore_id: str = ""
    n_obs: str = ""
    n_genes: str = ""
    kind: str = ""
    disease: str = ""

    @property
    def h5ad(self):
        return self.section if self.section.endswith(".h5ad") else f"{self.section}.h5ad"

    @property
    def stem(self):
        name = self.section
        if name.endswith(".h5ad"):
            name = name[:-5]
        return name

    @property
    def dataset_id(self):
        eid = (self.explore_id or "").strip()
        if eid:
            return eid
        stem = self.stem
        return stem if stem.startswith("CIMA_") else f"CIMA_{stem}"

    @property
    def tissues(self):
        return [t.strip() for t in self.tissue.split(",") if t.strip()]


def find_catalog_path():
    return _find_catalog_path(legacy_basename="cima_list.tsv")


def load_catalog(path=None):
    path = path or find_catalog_path()
    if not path:
        raise FileNotFoundError(
            f"{CATALOG_BASENAME} or cima_list.tsv not found under scripts/ "
            "(or set STOMICS_CATALOG / CIMA_CATALOG / CIMA_LIST)."
        )
    entries = []
    merged = os.path.basename(path) == CATALOG_BASENAME or path.endswith(os.sep + CATALOG_BASENAME)
    for row in iter_catalog_rows(path, atlas="cima" if merged else None):
        section = (row.get("Section") or "").strip()
        if not section:
            continue
        entries.append(
            CimaEntry(
                section=section,
                sex=(row.get("Sex") or "").strip(),
                stage=(row.get("Developmental stage") or "").strip(),
                technology=(row.get("Technology") or "").strip(),
                tissue=(row.get("Tissue") or "").strip(),
                spatial_clustering=(row.get("Spatial clustering") or "").strip(),
                he=(row.get("H&E") or "").strip(),
                download=(row.get("Download") or "").strip(),
                explore_id=(row.get("ExploreId") or "").strip(),
                n_obs=(row.get("n_obs") or "").strip(),
                n_genes=(row.get("n_genes") or "").strip(),
                kind=(row.get("Kind") or "").strip(),
                disease=(row.get("Disease") or "").strip(),
            )
        )
    return entries


def _norm(s: str) -> str:
    return s.strip().lower().replace(" ", "_")


def resolve_dataset_ref(query):
    """Map user input (PBMCs / CIMA_B / B.h5ad) → dataset_id + catalog entry."""
    query = str(query).strip().rstrip("/")
    if not query:
        raise ValueError("Empty dataset query")

    try:
        catalog = load_catalog()
    except FileNotFoundError:
        catalog = []

    q = query
    q_lower = q.lower()

    if q.upper().startswith("CIMA_"):
        rest = q.split("_", 1)[1]
        dataset_id = f"CIMA_{rest}"
        entry = next(
            (
                e
                for e in catalog
                if e.dataset_id.lower() == dataset_id.lower()
                or e.explore_id.lower() == dataset_id.lower()
            ),
            None,
        )
        if entry:
            return entry.dataset_id, entry
        return dataset_id, None

    for e in catalog:
        if e.stem.lower() == q_lower or e.section.lower() == q_lower or e.h5ad.lower() == q_lower:
            return e.dataset_id, e
        if e.dataset_id.lower() == q_lower or e.explore_id.lower() == q_lower:
            return e.dataset_id, e

    matches = []
    for e in catalog:
        hay = " ".join([e.section, e.stem, e.stage, e.tissue, e.dataset_id, e.explore_id, e.kind]).lower()
        if q_lower in hay or _norm(q) in _norm(hay):
            matches.append(e)

    if len(matches) == 1:
        return matches[0].dataset_id, matches[0]
    if len(matches) > 1:
        lines = [f"  {e.dataset_id}  ({e.stem}, {e.tissue})" for e in matches[:15]]
        raise ValueError(
            f"Ambiguous dataset '{query}' — {len(matches)} matches:\n" + "\n".join(lines)
        )

    stem = q[:-5] if q.endswith(".h5ad") else q
    if stem.upper().startswith("CIMA_"):
        return stem if stem.startswith("CIMA_") else f"CIMA_{stem.split('_', 1)[-1]}", None
    return f"CIMA_{stem}", None


def search_catalog(*, stage=None, tissue=None, technology=None, sex=None, text=None):
    catalog = load_catalog()
    out = catalog
    if stage:
        s = stage.lower()
        out = [e for e in out if s in e.stage.lower() or s in e.stem.lower()]
    if tissue:
        t = tissue.lower()
        out = [
            e
            for e in out
            if any(t in x.lower() for x in e.tissues)
            or t in e.stem.lower()
            or t in e.section.lower()
        ]
    if technology:
        tech = technology.lower()
        out = [e for e in out if tech in e.technology.lower() or tech in e.kind.lower()]
    if sex:
        sx = sex.lower()
        out = [e for e in out if sx in e.sex.lower()]
    if text:
        q = text.lower()
        out = [
            e
            for e in out
            if q in e.section.lower()
            or q in e.stem.lower()
            or q in e.tissue.lower()
            or q in e.dataset_id.lower()
            or q in e.kind.lower()
        ]
    return out


def is_primary_section(entry: CimaEntry) -> bool:
    return True


def is_sagittal_section(entry: CimaEntry) -> bool:
    """Compatibility with hesta recommend_sample --slices-only (all CIMA views qualify)."""
    return True


def score_entry(entry: CimaEntry, *, tissue: str | None = None) -> float | None:
    score = 10.0
    # Prefer smaller lineage views over full PBMCs when tissue/lineage hinted
    stem = entry.stem.lower()
    if tissue:
        t = tissue.lower()
        if t in stem or any(t in x.lower() for x in entry.tissues):
            score += 40
        if stem == "pbmcs" and t not in ("blood", "pbmc", "pbmcs", "all"):
            score -= 15
    if stem == "pbmcs":
        score += 5  # default atlas overview
    try:
        n = int(str(entry.n_obs).replace(",", "") or "0")
        # mild preference for manageable size
        if 0 < n < 1_000_000:
            score += 8
        elif n >= 5_000_000:
            score -= 5
    except ValueError:
        pass
    return score
