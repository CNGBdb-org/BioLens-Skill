"""Unified dataset catalog TSV (HESTA + MOSTA in one file under datasets/)."""

from __future__ import annotations

import csv
import os
from typing import Iterable, Optional

CATALOG_BASENAME = "datasets_list.tsv"
MERGED_FIELDNAMES = (
    "Atlas",
    "Species",
    "Section",
    "Developmental stage",
    "Sex",
    "Technology",
    "Kind",
    "Tissue",
    "Disease",
    "Spatial clustering",
    "H&E",
    "Download",
    "ExploreId",
    "n_obs",
    "n_genes",
)

_DATASETS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


def datasets_dir() -> str:
    return _DATASETS_ROOT


def default_catalog_path() -> str:
    return os.path.join(_DATASETS_ROOT, CATALOG_BASENAME)


def _unique_paths(paths: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for p in paths:
        ap = os.path.abspath(p)
        if ap not in seen:
            seen.add(ap)
            out.append(ap)
    return out


def catalog_search_paths(*, legacy_basename: Optional[str] = None) -> list[str]:
    """Resolution order: env overrides → merged TSV → legacy per-atlas TSV."""
    paths: list[str] = []
    for var in ("STOMICS_CATALOG",):
        env = os.environ.get(var, "").strip()
        if env:
            paths.append(env)
    paths.append(default_catalog_path())
    paths.append(os.path.join(os.getcwd(), CATALOG_BASENAME))
    if legacy_basename:
        env_map = {
            "hesta_list.tsv": "HESTA_LIST",
            "mosta_list.tsv": "MOSTA_LIST",
            "mccsta_list.tsv": "MCCSTA_LIST",
        }
        for var in (env_map.get(legacy_basename, ""),):
            if not var:
                continue
            env = os.environ.get(var, "").strip()
            if env:
                paths.append(env)
        paths.append(os.path.join(os.getcwd(), legacy_basename))
        # Repo root (hesta-spatial/) when lists lived outside skills/
        paths.append(os.path.abspath(os.path.join(_DATASETS_ROOT, "..", "..", "..", legacy_basename)))
    return _unique_paths(paths)


def find_catalog_path(*, legacy_basename: Optional[str] = None) -> Optional[str]:
    for path in catalog_search_paths(legacy_basename=legacy_basename):
        if os.path.isfile(path):
            return path
    return None


def _is_merged_file(path: str, fieldnames: Optional[list[str]]) -> bool:
    if os.path.basename(path) == CATALOG_BASENAME:
        return True
    if fieldnames and "Atlas" in fieldnames:
        return True
    return False


def iter_catalog_rows(
    path: str,
    *,
    atlas: Optional[str] = None,
) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = reader.fieldnames or []
        merged = _is_merged_file(path, list(fieldnames))
        rows: list[dict[str, str]] = []
        for row in reader:
            if merged:
                row_atlas = (row.get("Atlas") or "").strip().lower()
                if atlas and atlas.strip().lower() != row_atlas:
                    continue
            rows.append({k: (v or "").strip() for k, v in row.items()})
        return rows
