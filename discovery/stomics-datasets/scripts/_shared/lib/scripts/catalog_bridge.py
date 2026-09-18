"""Lazy import of per-atlas catalog modules."""

from __future__ import annotations

import importlib

from atlas_registry import _CUSTOM_CATALOG, get_atlas


def catalog_module():
    name = get_atlas().name
    if name in _CUSTOM_CATALOG:
        try:
            return importlib.import_module(f"{name}_catalog")
        except ModuleNotFoundError:
            # Portable stomics-datasets ships no custom/<atlas>/; use merged TSV.
            return importlib.import_module("std_catalog")
    return importlib.import_module("std_catalog")


def __getattr__(name):
    return getattr(catalog_module(), name)
