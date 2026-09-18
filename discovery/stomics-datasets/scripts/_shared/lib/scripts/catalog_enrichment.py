"""Catalog sidecars: enrichment, literature, curated — join with datasets_list.tsv."""

from __future__ import annotations

import csv
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from atlas_registry import lookup_atlas
from catalog_io import default_catalog_path, find_catalog_path, iter_catalog_rows

_DATASETS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

ENRICHMENT_BASENAME = "datasets_enrichment.tsv"
LITERATURE_BASENAME = "datasets_literature.tsv"
CURATED_BASENAME = "datasets_curated.tsv"

ENRICHMENT_FIELDS = (
    "row_key",
    "api_mode",
    "default_obs",
    "obs_columns",
    "has_spatial",
    "has_umap",
    "has_he",
    "bin_size",
    "object_type",
    "size_tier",
    "stage_norm",
    "stage_order",
    "stage_kind",
    "organs_norm",
    "section_plane",
    "donor_id",
    "batch_id",
    "replicate",
    "condition",
    "markers_available",
    "n_groups_obs",
    "demo_safe",
    "de_ready",
    "qc_pass",
    "use_cases",
    "skill_tags",
    "keywords",
    "last_probed",
)

ATLAS_LITERATURE_CACHE_BASENAME = "atlas_literature_cache.json"

# Named atlas → backing STOmics portal id (for literature fetch).
NAMED_PORTAL_ATLAS: dict[str, str] = {
    "artista": "STDS0000056",
    "zesta": "STDS0000057",
    "mosta": "STDS0000058",
    "lista": "STDS0000059",
    "flysta3d": "STDS0000060",
    "soybean": "STDS0000168",
    "zebrafish_vrh": "STDS0000248",
    "hesta": "STDS0000394",
    "mccsta": "STDS0000395",
    "flysta3d-v2": "STDS0000398",
}

LITERATURE_FIELDS = (
    "row_key",
    "Atlas",
    "dataset_title",
    "pmid",
    "doi",
    "portal_url",
    "citation",
    "paper_figures",
)

CURATED_FIELDS = (
    "row_key",
    "demo_safe",
    "paper_figures",
    "notes",
    "skill_tags_verified",
)

# Named atlas literature (from README / gene_tables)
ATLAS_LITERATURE: dict[str, dict[str, str]] = {
    "hesta": {
        "doi": "10.1038/s41586-026-10545-0",
        "citation": "HESTA human embryonic spatiotemporal atlas (Stereo-seq)",
        "portal_url": "https://db.cngb.org/hesta/",
    },
    "mosta": {
        "doi": "10.1016/j.cell.2022.04.003",
        "citation": "MOSTA mouse embryonic spatial atlas",
        "portal_url": "https://db.cngb.org/stomics/mosta/",
    },
    "mccsta": {
        "doi": "10.1126/science.aea2673",
        "citation": "MCCSTA marmoset cortical spatial atlas",
        "portal_url": "https://db.cngb.org/stomics/mccsta/",
    },
    "cima": {
        "doi": "10.1126/science.adt3130",
        "citation": "CIMA TrueBlood immune multi-omics atlas",
        "portal_url": "https://db.cngb.org/trueblood/cima/",
    },
    "cbmsta": {
        "doi": "10.1126/science.ado3927",
        "citation": "Cross-species cerebellar Stereo-seq / snRNA atlas (CBMSTA)",
        "portal_url": "https://db.cngb.org/stomics/cbmsta/",
    },
    "lista": {
        "doi": "10.1038/s41588-024-01709-7",
        "citation": "LISTA mouse liver spatial regeneration atlas",
        "portal_url": "https://db.cngb.org/stomics/lista/",
    },
    "cirsta": {
        "doi": "10.1038/s41588-024-01687-w",
        "citation": "CIRSTA mouse cholestatic injury spatial atlas",
        "portal_url": "https://db.cngb.org/stomics/cirsta/",
    },
}

# Demo-safe samples for live Web demos
CURATED_DEMO: dict[str, dict[str, str]] = {
    "hesta|CS12-13_E1S1_HESTA.h5ad": {
        "demo_safe": "1",
        "notes": "Small HESTA slice; celltype / expression demos",
        "skill_tags_verified": "gene_expression;plot_spatial_clusters;list_obs_groups",
    },
    "hesta|CS23_E2S8_HESTA.h5ad": {
        "demo_safe": "1",
        "paper_figures": "Fig.1b;representative",
        "notes": "HESTA flagship sagittal slice",
        "skill_tags_verified": "gene_expression;plot_spatial_clusters;gene_across_samples",
    },
    "hesta|CS17_E1S3_HESTA.h5ad": {
        "demo_safe": "1",
        "paper_figures": "Fig.3",
        "notes": "Cardiac / SAN panel demos",
        "skill_tags_verified": "gene_expression;paper_panel;disease_gene_map",
    },
    "mosta|E16.5_E1S1.MOSTA.h5ad": {
        "demo_safe": "1",
        "notes": "MOSTA standard spatial demo",
        "skill_tags_verified": "gene_expression;plot_spatial_clusters",
    },
    "mccsta|T530.h5ad": {
        "demo_safe": "1",
        "notes": "MCCSTA auditory cortex slice",
        "skill_tags_verified": "gene_expression;compare_organs_gene",
    },
}

_GSM_RE = re.compile(r"(GSM\d+)", re.I)
_REP_RE = re.compile(r"rep(\d+)", re.I)
_CIMA_DONOR_RE = re.compile(r"CIMA_H\d+", re.I)
_CS_STAGE_RE = re.compile(r"CS(\d+(?:-\d+)?)", re.I)
_E_STAGE_RE = re.compile(r"E(\d+\.?\d*)", re.I)
_PCW_RE = re.compile(r"PCW\s*(\d+)", re.I)
_BIN_RE = re.compile(r"bin(\d+)", re.I)
_ANATOMY_STAGE_HINTS = re.compile(
    r"section|coronal|sagittal|lobe|bulb|cortex|cord|colon|lung|skin|heart|brain\b|kidney|"
    r"ileum|embryo|neonatal|adult|tumor|cancer|carcinoma",
    re.I,
)

ORGAN_ALIASES = {
    "brain": "Brain",
    "heart": "Heart",
    "liver": "Liver",
    "lung": "Lung",
    "kidney": "Kidney",
    "eye": "Eye",
    "muscle": "Muscle",
    "stomach": "Stomach",
    "intestine": "Intestine",
    "spleen": "Spleen",
    "embryo": "Embryo",
    "skin": "Skin",
    "pancreas": "Pancreas",
    "gonad": "Gonad",
}


def datasets_dir() -> str:
    return _DATASETS_ROOT


def enrichment_path() -> str:
    return os.path.join(_DATASETS_ROOT, ENRICHMENT_BASENAME)


def literature_path() -> str:
    return os.path.join(_DATASETS_ROOT, LITERATURE_BASENAME)


def curated_path() -> str:
    return os.path.join(_DATASETS_ROOT, CURATED_BASENAME)


def row_key(atlas: str, section: str) -> str:
    return f"{(atlas or '').strip().lower()}|{(section or '').strip()}"


def _parse_int(s: str) -> int | None:
    try:
        return int(str(s).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def size_tier_from_n_obs(n_obs: int | None) -> str:
    if n_obs is None:
        return ""
    if n_obs < 500:
        return "tiny"
    if n_obs < 5_000:
        return "small"
    if n_obs < 50_000:
        return "medium"
    if n_obs < 500_000:
        return "large"
    return "huge"


def infer_object_type(section: str, kind: str) -> str:
    s = (section or "").lower()
    k = (kind or "").lower()
    if "substructure" in s or ".bin50." in s:
        return "substructure"
    if "snrna" in s.replace("_", "") or k == "snrna":
        return "snrna"
    if "3d" in s and "hesta" in s:
        return "integrated"
    if any(x in s for x in ("all_stage", "allstage", "integrated", "combined")):
        return "integrated"
    if k in ("spatial", "sagittal", "coronal_bin200", "sagittal_bin200"):
        return "slice"
    if k == "ftp_only":
        return "other"
    return "slice" if k == "spatial" else (k or "other")


def infer_bin_size(section: str, technology: str) -> str:
    s = (section or "").lower()
    m = _BIN_RE.search(s)
    if m:
        return m.group(1)
    if "bin50" in s or "substructure" in s:
        return "50"
    if "bin200" in s or "mbcsta" in s:
        return "200"
    tech = (technology or "").lower()
    if "visium" in tech or "spatial transcriptomics" in tech:
        return "spot"
    if "slide-seq" in tech:
        return "bead"
    if "stereo" in tech or "stomics" in tech or "st " == tech[:3]:
        return "cell"
    if tech in ("scrna-seq", "scrna", "snrna"):
        return "cell"
    return ""


def infer_section_plane(section: str, atlas: str) -> str:
    s = (section or "").lower()
    if "3d" in s:
        return "3d"
    if "coronal" in s or "coro" in s:
        return "coronal"
    if atlas.lower() in ("hesta", "mosta", "mccsta"):
        if "substructure" not in s and s.endswith((".h5ad", "_hesta.h5ad", ".mosta.h5ad")):
            return "sagittal"
    return "other"


def classify_stage_kind(stage: str, section: str) -> str:
    """developmental | anatomy | tissue_label | other."""
    raw = (stage or "").strip()
    sec = section or ""
    if not raw:
        return "other"
    if _CS_STAGE_RE.search(raw) or _E_STAGE_RE.search(raw) or _PCW_RE.search(raw):
        return "developmental"
    if _CS_STAGE_RE.search(sec) or _E_STAGE_RE.search(sec):
        return "developmental"
    low = raw.lower()
    if _ANATOMY_STAGE_HINTS.search(raw):
        return "anatomy"
    if len(raw) < 48 and raw[0].isupper() and "," not in raw and ";" not in raw:
        return "tissue_label"
    if any(x in low for x in ("week", "day", "month", "year", "gestation", "pcw")):
        return "developmental"
    return "other"


def normalize_stage(stage: str, section: str) -> tuple[str, str, str]:
    """Return (stage_norm, stage_order, stage_kind)."""
    stage = (stage or "").strip()
    section = section or ""
    kind = classify_stage_kind(stage, section)
    if stage and stage.lower() not in ("", "nan"):
        order = ""
        m = _CS_STAGE_RE.search(stage) or _CS_STAGE_RE.search(section)
        if m:
            base = m.group(1).split("-")[0]
            try:
                order = str(int(base))
            except ValueError:
                order = base
            return f"CS{m.group(1)}", order, "developmental"
        m = _E_STAGE_RE.search(stage) or _E_STAGE_RE.search(section)
        if m:
            return f"E{m.group(1)}", m.group(1), "developmental"
        if kind == "developmental":
            return stage, "", kind
        return stage, "", kind
    m = _CS_STAGE_RE.search(section)
    if m:
        return f"CS{m.group(1)}", m.group(1).split("-")[0], "developmental"
    m = _E_STAGE_RE.search(section)
    if m:
        return f"E{m.group(1)}", m.group(1), "developmental"
    return "", "", kind


def normalize_organs(tissue: str) -> str:
    if not tissue:
        return ""
    parts = []
    for chunk in re.split(r"[,;/|]", tissue):
        t = chunk.strip()
        if not t:
            continue
        low = t.lower()
        matched = False
        for alias, canon in ORGAN_ALIASES.items():
            if alias in low:
                parts.append(canon)
                matched = True
                break
        if not matched and len(t) < 40:
            parts.append(t.title())
    seen: list[str] = []
    for p in parts:
        if p not in seen:
            seen.append(p)
    return ";".join(seen[:30])


def parse_donor_replicate(section: str) -> tuple[str, str, str]:
    s = section or ""
    donor = ""
    m = _GSM_RE.search(s)
    if m:
        donor = m.group(1).upper()
    m = _CIMA_DONOR_RE.search(s)
    if m:
        donor = m.group(0).upper()
    rep = ""
    m = _REP_RE.search(s)
    if m:
        rep = f"rep{m.group(1)}"
    batch = donor or ""
    return donor, batch, rep


def infer_api_mode(row: dict[str, str]) -> str:
    eid = (row.get("ExploreId") or "").strip()
    dl = (row.get("Download") or "").strip()
    if eid:
        return "parquet"
    if dl.lower().endswith(".h5ad"):
        return "h5ad_only"
    return "none"


def infer_default_obs(atlas: str) -> str:
    spec = lookup_atlas(atlas)
    if spec:
        return spec.default_obs_label or ""
    return ""


def infer_use_cases(row: dict[str, str], enrichment: dict[str, str]) -> str:
    cases: list[str] = []
    kind = (row.get("Kind") or "").lower()
    if kind == "spatial" or enrichment.get("has_spatial") == "1":
        cases.append("expression")
        cases.append("cluster")
    if kind == "snrna":
        cases.append("scrna")
    if (row.get("Disease") or "").strip():
        cases.append("disease")
    if enrichment.get("de_ready") == "1":
        cases.append("de")
    if (row.get("H&E") or "").strip():
        cases.append("he_overlay")
    return ";".join(dict.fromkeys(cases))


def infer_skill_tags(row: dict[str, str], enrichment: dict[str, str]) -> str:
    tags: list[str] = ["dataset_info", "list_datasets"]
    mode = enrichment.get("api_mode") or infer_api_mode(row)
    obj = enrichment.get("object_type") or infer_object_type(row.get("Section", ""), row.get("Kind", ""))
    if mode == "parquet" and obj in ("slice", "substructure"):
        tags.extend([
            "gene_expression",
            "plot_spatial_clusters",
            "list_obs_groups",
            "list_markers",
        ])
    if mode == "parquet":
        tags.append("gene_across_samples")
    if (row.get("Disease") or "").strip():
        tags.append("disease_gene_map")
    atlas = (row.get("Atlas") or "").lower()
    if atlas in ("hesta", "mosta", "mccsta"):
        tags.append("recommend_sample")
    if enrichment.get("de_ready") == "1":
        tags.append("de_two_groups")
    return ";".join(dict.fromkeys(tags))


def infer_de_ready(row: dict[str, str], n_obs: int | None) -> str:
    if n_obs is None or n_obs < 200:
        return "0"
    kind = (row.get("Kind") or "").lower()
    if kind not in ("spatial", "snrna", "sagittal", "coronal_bin200", "sagittal_bin200", ""):
        return "0"
    donor, _, rep = parse_donor_replicate(row.get("Section", ""))
    if donor and rep:
        return "1"
    disease = (row.get("Disease") or "").strip()
    if disease and n_obs >= 500:
        return "1"
    if n_obs >= 500 and n_obs <= 80_000:
        return "1"
    return "0"


def atlas_literature_cache_path() -> str:
    return os.path.join(_DATASETS_ROOT, ATLAS_LITERATURE_CACHE_BASENAME)


_atlas_lit_cache: dict[str, dict[str, str]] | None = None


def load_atlas_literature_cache() -> dict[str, dict[str, str]]:
    global _atlas_lit_cache
    if _atlas_lit_cache is not None:
        return _atlas_lit_cache
    path = atlas_literature_cache_path()
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            _atlas_lit_cache = {str(k).lower(): v for k, v in raw.items()}
            return _atlas_lit_cache
    _atlas_lit_cache = {}
    return _atlas_lit_cache


def save_atlas_literature_cache(data: dict[str, dict[str, str]]) -> str:
    global _atlas_lit_cache
    path = atlas_literature_cache_path()
    normalized = {str(k).lower(): v for k, v in sorted(data.items())}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(normalized, f, ensure_ascii=False, indent=2)
    _atlas_lit_cache = normalized
    return path


def resolve_portal_atlas_id(atlas: str) -> str:
    atlas_l = (atlas or "").strip().lower()
    if atlas_l.startswith("stds") or atlas_l.startswith("scds"):
        return atlas_l.upper()
    return NAMED_PORTAL_ATLAS.get(atlas_l, "")


def atlas_literature_for(atlas: str, registry: dict[str, dict] | None = None) -> dict[str, str]:
    atlas_l = (atlas or "").strip().lower()
    lit = dict(ATLAS_LITERATURE.get(atlas_l, {}))
    cache = load_atlas_literature_cache()
    portal_id = resolve_portal_atlas_id(atlas)
    for key in (atlas_l, portal_id.lower(), portal_id.upper()):
        if key and key in cache:
            for k, v in cache[key].items():
                if v and not lit.get(k):
                    lit[k] = v
    if not lit.get("doi") and not lit.get("pmid"):
        for row in load_literature_index().values():
            if (row.get("Atlas") or "").strip().lower() != atlas_l:
                continue
            for k in ("doi", "pmid", "citation", "portal_url", "dataset_title"):
                if row.get(k) and not lit.get(k if k != "dataset_title" else k):
                    lit[k] = row[k]
            if lit.get("doi") or lit.get("pmid"):
                break
    if registry:
        reg = registry.get(atlas.upper()) or registry.get(atlas) or registry.get(atlas_l) or {}
        for k in ("doi", "pmid", "citation", "portal_url", "display"):
            if reg.get(k) and not lit.get(k if k != "display" else "dataset_title"):
                lit["dataset_title" if k == "display" else k] = reg[k]
    return lit


def build_keywords(row: dict[str, str], enrichment: dict[str, str]) -> str:
    bits = [
        row.get("Atlas", ""),
        row.get("Species", ""),
        row.get("Technology", ""),
        row.get("Kind", ""),
        row.get("Tissue", ""),
        row.get("Disease", ""),
        enrichment.get("stage_norm", ""),
        enrichment.get("organs_norm", ""),
        enrichment.get("object_type", ""),
    ]
    return ";".join(x for x in bits if x)[:500]


def derive_enrichment_row(row: dict[str, str], *, api_probe: dict[str, Any] | None = None) -> dict[str, str]:
    """Rule-based enrichment; optional api_probe from index.json.gz."""
    atlas = (row.get("Atlas") or "").strip()
    section = (row.get("Section") or "").strip()
    rk = row_key(atlas, section)
    n_obs = _parse_int(row.get("n_obs", ""))
    stage_norm, stage_order, stage_kind = normalize_stage(row.get("Developmental stage", ""), section)
    donor, batch, rep = parse_donor_replicate(section)
    api_mode = infer_api_mode(row)
    default_obs = infer_default_obs(atlas)
    obj_type = infer_object_type(section, row.get("Kind", ""))
    kind = (row.get("Kind") or "").lower()
    has_he = "1" if (row.get("H&E") or "").strip().startswith("http") else "0"
    infer_umap = kind == "snrna" and api_mode == "parquet"

    out: dict[str, str] = {
        "row_key": rk,
        "api_mode": api_mode,
        "default_obs": default_obs,
        "obs_columns": "",
        "has_spatial": "1" if api_mode == "parquet" and obj_type in ("slice", "substructure") else "0",
        "has_umap": "1" if infer_umap else "0",
        "has_he": has_he,
        "bin_size": infer_bin_size(section, row.get("Technology", "")),
        "object_type": obj_type,
        "size_tier": size_tier_from_n_obs(n_obs),
        "stage_norm": stage_norm,
        "stage_order": stage_order,
        "stage_kind": stage_kind,
        "organs_norm": normalize_organs(row.get("Tissue", "")),
        "section_plane": infer_section_plane(section, atlas),
        "donor_id": donor,
        "batch_id": batch,
        "replicate": rep,
        "condition": (row.get("Disease") or "").strip()[:200],
        "markers_available": "",
        "n_groups_obs": "",
        "demo_safe": "0",
        "de_ready": infer_de_ready(row, n_obs),
        "qc_pass": "1",
        "use_cases": "",
        "skill_tags": "",
        "keywords": "",
        "last_probed": "",
    }

    if api_probe:
        out["last_probed"] = api_probe.get("last_probed", "")
        if api_probe.get("obs_columns"):
            out["obs_columns"] = api_probe["obs_columns"]
        if api_probe.get("default_obs"):
            out["default_obs"] = api_probe["default_obs"]
        if api_probe.get("has_spatial") is not None:
            out["has_spatial"] = "1" if api_probe["has_spatial"] else "0"
        if api_probe.get("has_umap") is not None:
            out["has_umap"] = "1" if api_probe["has_umap"] else "0"
        if api_probe.get("markers_available"):
            out["markers_available"] = api_probe["markers_available"]
        if api_probe.get("n_groups_obs") is not None:
            out["n_groups_obs"] = str(api_probe["n_groups_obs"])

    curated = CURATED_DEMO.get(rk, {})
    if curated.get("demo_safe") == "1":
        out["demo_safe"] = "1"
    out["use_cases"] = infer_use_cases(row, out)
    out["skill_tags"] = infer_skill_tags(row, out)
    out["keywords"] = build_keywords(row, out)
    return out


def build_literature_row(row: dict[str, str], registry: dict[str, dict] | None = None) -> dict[str, str]:
    atlas = (row.get("Atlas") or "").strip()
    section = (row.get("Section") or "").strip()
    rk = row_key(atlas, section)
    atlas_l = atlas.lower()
    lit = atlas_literature_for(atlas, registry)
    title = lit.get("dataset_title", "")
    portal = (row.get("Spatial clustering") or "").strip()
    if portal and "db.cngb.org" in portal and "/datasets/" in portal:
        portal = portal.split("?")[0]
    if registry and not title:
        reg = registry.get(atlas.upper()) or registry.get(atlas) or {}
        if reg.get("display"):
            title = reg["display"]
        if reg.get("portal") and not lit.get("portal_url"):
            lit["portal_url"] = reg["portal"]
    if not title and atlas_l in ATLAS_LITERATURE:
        title = lit.get("citation", atlas)
    if not portal and lit.get("portal_url"):
        portal = lit["portal_url"]
    return {
        "row_key": rk,
        "Atlas": atlas,
        "dataset_title": title[:300],
        "pmid": lit.get("pmid", ""),
        "doi": lit.get("doi", ""),
        "portal_url": portal[:300] or lit.get("portal_url", "")[:300],
        "citation": lit.get("citation", "")[:300],
        "paper_figures": "",
    }


def build_curated_row(row: dict[str, str]) -> dict[str, str]:
    rk = row_key(row.get("Atlas", ""), row.get("Section", ""))
    c = CURATED_DEMO.get(rk, {})
    return {
        "row_key": rk,
        "demo_safe": c.get("demo_safe", "0"),
        "paper_figures": c.get("paper_figures", ""),
        "notes": c.get("notes", ""),
        "skill_tags_verified": c.get("skill_tags_verified", ""),
    }


def _read_sidecar(path: str, fields: tuple[str, ...]) -> dict[str, dict[str, str]]:
    if not os.path.isfile(path):
        return {}
    out: dict[str, dict[str, str]] = {}
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            rk = (row.get("row_key") or "").strip()
            if rk:
                out[rk] = {k: (row.get(k) or "").strip() for k in fields}
    return out


_enrichment_cache: dict[str, dict[str, str]] | None = None
_literature_cache: dict[str, dict[str, str]] | None = None
_curated_cache: dict[str, dict[str, str]] | None = None


def load_enrichment_index() -> dict[str, dict[str, str]]:
    global _enrichment_cache
    if _enrichment_cache is None:
        _enrichment_cache = _read_sidecar(enrichment_path(), ENRICHMENT_FIELDS)
    return _enrichment_cache


def load_literature_index() -> dict[str, dict[str, str]]:
    global _literature_cache
    if _literature_cache is None:
        _literature_cache = _read_sidecar(literature_path(), LITERATURE_FIELDS)
    return _literature_cache


def load_curated_index() -> dict[str, dict[str, str]]:
    global _curated_cache
    if _curated_cache is None:
        _curated_cache = _read_sidecar(curated_path(), CURATED_FIELDS)
    return _curated_cache


def clear_catalog_sidecar_cache() -> None:
    global _enrichment_cache, _literature_cache, _curated_cache
    _enrichment_cache = _literature_cache = _curated_cache = None


def merge_catalog_row(row: dict[str, str]) -> dict[str, str]:
    """Base catalog row + enrichment + literature + curated."""
    rk = row_key(row.get("Atlas", ""), row.get("Section", ""))
    merged = dict(row)
    merged["row_key"] = rk
    for key, idx in (
        ("enrichment", load_enrichment_index()),
        ("literature", load_literature_index()),
        ("curated", load_curated_index()),
    ):
        extra = idx.get(rk, {})
        for k, v in extra.items():
            if k == "row_key":
                continue
            merged[k] = v
    return merged


def iter_merged_catalog(
    path: str | None = None,
    *,
    atlas: str | None = None,
) -> list[dict[str, str]]:
    cat_path = path or find_catalog_path() or default_catalog_path()
    rows = iter_catalog_rows(cat_path, atlas=atlas)
    return [merge_catalog_row(r) for r in rows]


@dataclass
class CatalogFilter:
    atlas: str | None = None
    species: str | None = None
    tissue: str | None = None
    organ: str | None = None
    stage: str | None = None
    kind: str | None = None
    disease: str | None = None
    text: str | None = None
    api_mode: str | None = None
    has_spatial: bool | None = None
    has_umap: bool | None = None
    demo_safe: bool | None = None
    de_ready: bool | None = None
    size_tier: str | None = None
    object_type: str | None = None
    section_plane: str | None = None
    skill_tag: str | None = None
    use_case: str | None = None
    pmid: str | None = None
    doi: str | None = None
    donor_id: str | None = None
    min_obs: int | None = None
    max_obs: int | None = None
    limit: int = 0


def _match_bool_field(val: str, want: bool | None) -> bool:
    if want is None:
        return True
    return (val == "1") == want


def filter_merged_rows(rows: Iterable[dict[str, str]], flt: CatalogFilter) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for row in rows:
        if flt.atlas and flt.atlas.lower() not in (row.get("Atlas") or "").lower():
            continue
        if flt.species and flt.species.lower() not in (row.get("Species") or "").lower():
            continue
        if flt.kind and flt.kind.lower() not in (row.get("Kind") or "").lower():
            continue
        if flt.api_mode and flt.api_mode.lower() != (row.get("api_mode") or infer_api_mode(row)).lower():
            continue
        if not _match_bool_field(row.get("has_spatial", ""), flt.has_spatial):
            continue
        if not _match_bool_field(row.get("has_umap", ""), flt.has_umap):
            continue
        if not _match_bool_field(row.get("demo_safe", ""), flt.demo_safe):
            continue
        if not _match_bool_field(row.get("de_ready", ""), flt.de_ready):
            continue
        if flt.size_tier and flt.size_tier.lower() != (row.get("size_tier") or "").lower():
            continue
        if flt.object_type and flt.object_type.lower() != (row.get("object_type") or "").lower():
            continue
        if flt.section_plane and flt.section_plane.lower() != (row.get("section_plane") or "").lower():
            continue
        if flt.disease and flt.disease.lower() not in (row.get("Disease") or "").lower():
            continue
        if flt.donor_id and flt.donor_id.upper() not in (row.get("donor_id") or "").upper():
            continue
        if flt.pmid and flt.pmid not in (row.get("pmid") or ""):
            continue
        if flt.doi and flt.doi.lower() not in (row.get("doi") or "").lower():
            continue
        if flt.tissue or flt.organ:
            needle = (flt.organ or flt.tissue or "").lower()
            hay = " ".join([
                row.get("Tissue", ""),
                row.get("organs_norm", ""),
            ]).lower()
            if needle not in hay:
                continue
        if flt.stage:
            st = flt.stage.lower()
            if st not in (row.get("Developmental stage") or "").lower() and st not in (row.get("stage_norm") or "").lower():
                if st not in (row.get("Section") or "").lower():
                    continue
        if flt.skill_tag:
            tag = flt.skill_tag.lower()
            if tag not in (row.get("skill_tags") or "").lower() and tag not in (row.get("skill_tags_verified") or "").lower():
                continue
        if flt.use_case:
            uc = flt.use_case.lower()
            if uc not in (row.get("use_cases") or "").lower():
                continue
        if flt.text:
            q = flt.text.lower()
            blob = " ".join(str(row.get(k, "")) for k in row).lower()
            if q not in blob:
                continue
        n_obs = _parse_int(row.get("n_obs", ""))
        if flt.min_obs is not None and (n_obs is None or n_obs < flt.min_obs):
            continue
        if flt.max_obs is not None and (n_obs is None or n_obs > flt.max_obs):
            continue
        out.append(row)
    if flt.limit and len(out) > flt.limit:
        return out[: flt.limit]
    return out


def load_stds_registry() -> dict[str, dict]:
    path = os.path.join(_DATASETS_ROOT, "stds_registry.json")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def load_cdcp_registry() -> dict[str, dict]:
    path = os.path.join(_DATASETS_ROOT, "cdcp_registry.json")
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def combined_registry() -> dict[str, dict]:
    reg: dict[str, dict] = {}
    reg.update(load_stds_registry())
    reg.update(load_cdcp_registry())
    for k, v in ATLAS_LITERATURE.items():
        reg.setdefault(k, {}).update(v)
    return reg
