"""CIMA atlas configuration (standalone skill)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

_SCRIPTS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_OBS_LABEL = "cell_type_l4"


@dataclass(frozen=True)
class AtlasSpec:
    name: str
    api_prefix: str
    cache_env_var: str
    use_local_env_var: str
    default_obs_label: str
    fuzzy_gene_symbols: bool
    catalog_list_name: str
    display_name: str
    species: str = ""
    catalog_atlas: str = ""
    portal_url: str = ""
    visual_engine: str = ""


CIMA = AtlasSpec(
    name="cima",
    api_prefix="CIMA_",
    cache_env_var="CIMA_CACHE",
    use_local_env_var="CIMA_USE_LOCAL",
    default_obs_label="cell_type_l4",
    fuzzy_gene_symbols=False,
    catalog_list_name="catalog.tsv",
    display_name="CIMA (TrueBlood)",
    species="人",
    catalog_atlas="cima",
    portal_url="https://db.cngb.org/trueblood/cima/",
    visual_engine="explore",
)


def scripts_root() -> str:
    return _SCRIPTS_ROOT


def datasets_root() -> str:
    return _SCRIPTS_ROOT


def shared_lib_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def atlas_root(atlas: Optional[str] = None) -> Optional[str]:
    return _SCRIPTS_ROOT


def atlas_lib_dir(atlas: Optional[str] = None) -> Optional[str]:
    lib = os.path.join(_SCRIPTS_ROOT, "_lib")
    return lib if os.path.isdir(lib) else None


def shared_root() -> str:
    return _SCRIPTS_ROOT


def get_atlas() -> AtlasSpec:
    return CIMA


def set_atlas(name: str) -> AtlasSpec:
    global DEFAULT_OBS_LABEL
    key = (name or "").strip().lower()
    if key not in ("", "cima"):
        raise ValueError(f"This skill only supports atlas 'cima', got {name!r}")
    DEFAULT_OBS_LABEL = CIMA.default_obs_label
    os.environ["STOMICS_ATLAS"] = "cima"
    return CIMA


def lookup_atlas(name: str) -> Optional[AtlasSpec]:
    key = (name or "").strip().lower()
    if key in ("", "cima"):
        return CIMA
    return None


def list_atlas_names() -> list[str]:
    return ["cima"]


def detect_atlas_from_path(path: str) -> Optional[str]:
    return "cima"


def resolve_dataset_ref(data_dir: str):
    import catalog_bridge as cat

    return cat.resolve_dataset_ref(data_dir)


def catalog_path() -> str:
    from catalog_io import default_catalog_path

    return default_catalog_path()
