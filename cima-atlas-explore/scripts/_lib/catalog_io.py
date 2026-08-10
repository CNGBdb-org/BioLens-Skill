"""CIMA sample catalog TSV under scripts/."""

from __future__ import annotations

import csv
import os
from typing import Iterable, Optional

CATALOG_BASENAME = "catalog.tsv"
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

_SCRIPTS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def datasets_dir() -> str:
    return _SCRIPTS_ROOT


def default_catalog_path() -> str:
    return os.path.join(_SCRIPTS_ROOT, CATALOG_BASENAME)


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
    """Resolution order: env overrides → scripts/catalog.tsv → cwd / legacy names."""
    paths: list[str] = []
    for var in ("CIMA_CATALOG", "STOMICS_CATALOG", "CIMA_LIST"):
        env = os.environ.get(var, "").strip()
        if env:
            paths.append(env)
    paths.append(default_catalog_path())
    paths.append(os.path.join(os.getcwd(), CATALOG_BASENAME))
    for legacy in ("datasets_list.tsv", "cima_list.tsv"):
        paths.append(os.path.join(_SCRIPTS_ROOT, legacy))
        paths.append(os.path.join(os.getcwd(), legacy))
    if legacy_basename:
        paths.append(os.path.join(_SCRIPTS_ROOT, legacy_basename))
        paths.append(os.path.join(os.getcwd(), legacy_basename))
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
