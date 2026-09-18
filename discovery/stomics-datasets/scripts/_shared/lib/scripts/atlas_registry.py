"""Atlas configuration for CNGB STOmics parquet atlases."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from typing import Optional

_DATASETS_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_STDS_REGISTRY_JSON = os.path.join(_DATASETS_ROOT, "stds_registry.json")
_CDCP_REGISTRY_JSON = os.path.join(_DATASETS_ROOT, "cdcp_registry.json")
_PORTAL_REGISTRY_JSON = os.path.join(_DATASETS_ROOT, "portal_atlas_registry.json")
_STDS_NAME_RE = re.compile(r"^STDS\d{7}$", re.I)
_SCDS_NAME_RE = re.compile(r"^SCDS\d{7}$", re.I)
_stds_meta_cache: Optional[dict[str, dict]] = None
_cdcp_meta_cache: Optional[dict[str, dict]] = None
_portal_meta_cache: Optional[dict[str, dict]] = None


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
    catalog_atlas: str = ""  # if set, filter datasets_list.tsv by this Atlas column
    portal_url: str = ""
    visual_engine: str = ""  # explore | cirro | portal_spa


ATLASES: dict[str, AtlasSpec] = {
    "hesta": AtlasSpec(
        name="hesta", api_prefix="embryodev_", cache_env_var="HESTA_CACHE", use_local_env_var="HESTA_USE_LOCAL",
        default_obs_label="celltype", fuzzy_gene_symbols=False, catalog_list_name="datasets_list.tsv",
        display_name="HESTA", species="人",
    ),
    "mosta": AtlasSpec(
        name="mosta", api_prefix="STDS0000058_", cache_env_var="MOSTA_CACHE", use_local_env_var="MOSTA_USE_LOCAL",
        default_obs_label="annotation", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="MOSTA", species="小鼠",
    ),
    "mccsta": AtlasSpec(
        name="mccsta", api_prefix="MBCSTA_", cache_env_var="MCCSTA_CACHE", use_local_env_var="MCCSTA_USE_LOCAL",
        default_obs_label="annotation", fuzzy_gene_symbols=False, catalog_list_name="datasets_list.tsv",
        display_name="MCCSTA", species="狨猴",
    ),
    "artista": AtlasSpec(
        name="artista", api_prefix="STDS0000056_", cache_env_var="ARTISTA_CACHE", use_local_env_var="ARTISTA_USE_LOCAL",
        default_obs_label="Annotation", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="ARTISTA", species="墨西哥钝口蝾螈（蝾螈）",
    ),
    "cbmsta": AtlasSpec(
        name="cbmsta", api_prefix="CBMSTA_", cache_env_var="CBMSTA_CACHE", use_local_env_var="CBMSTA_USE_LOCAL",
        default_obs_label="region", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="CBMSTA", species="小鼠 / 狨猴 / 猕猴",
    ),
    "cirsta": AtlasSpec(
        name="cirsta", api_prefix="CIRSTA_", cache_env_var="CIRSTA_CACHE", use_local_env_var="CIRSTA_USE_LOCAL",
        default_obs_label="annotation", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="CIRSTA", species="小鼠",
    ),
    "ctsta": AtlasSpec(
        name="ctsta", api_prefix="CTSTA_", cache_env_var="CTSTA_CACHE", use_local_env_var="CTSTA_USE_LOCAL",
        default_obs_label="final_clusters", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="CTSTA", species="黄瓜 / 番茄",
    ),
    "flysta3d": AtlasSpec(
        name="flysta3d", api_prefix="STDS0000060_", cache_env_var="FLYSTA3D_CACHE", use_local_env_var="FLYSTA3D_USE_LOCAL",
        default_obs_label="annotation", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="FlySTA3D", species="果蝇",
    ),
    "flysta3d-v2": AtlasSpec(
        name="flysta3d-v2", api_prefix="STDS0000398_", cache_env_var="FLYSTA3D_V2_CACHE", use_local_env_var="FLYSTA3D_V2_USE_LOCAL",
        default_obs_label="annotation", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="FlySTA3D v2", species="果蝇",
    ),
    "lista": AtlasSpec(
        name="lista", api_prefix="STDS0000059_", cache_env_var="LISTA_CACHE", use_local_env_var="LISTA_USE_LOCAL",
        default_obs_label="annotation", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="LISTA", species="小鼠",
    ),
    "mdesta": AtlasSpec(
        name="mdesta", api_prefix="cron_", cache_env_var="MDESTA_CACHE", use_local_env_var="MDESTA_USE_LOCAL",
        default_obs_label="cell_type", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="MDESTA", species="玉米",
    ),
    "mpsta": AtlasSpec(
        name="mpsta", api_prefix="MPSTA_", cache_env_var="MPSTA_CACHE", use_local_env_var="MPSTA_USE_LOCAL",
        default_obs_label="subregion", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="MPSTA", species="小鼠",
    ),
    "prista4d": AtlasSpec(
        name="prista4d", api_prefix="PRISTA4D_", cache_env_var="PRISTA4D_CACHE", use_local_env_var="PRISTA4D_USE_LOCAL",
        default_obs_label="region", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="PRISTA4D", species="涡虫",
    ),
    "soybean": AtlasSpec(
        name="soybean", api_prefix="STDS0000168_", cache_env_var="SOYBEAN_CACHE", use_local_env_var="SOYBEAN_USE_LOCAL",
        default_obs_label="celltype", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="Soybean STA", species="大豆",
    ),
    "stmich": AtlasSpec(
        name="stmich", api_prefix="stmich_", cache_env_var="STMICH_CACHE", use_local_env_var="STMICH_USE_LOCAL",
        default_obs_label="region", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="STMICH", species="小鼠",
    ),
    "zebrafish_VRH": AtlasSpec(
        name="zebrafish_VRH", api_prefix="STDS0000248_", cache_env_var="ZEBRAFISH_VRH_CACHE", use_local_env_var="ZEBRAFISH_VRH_USE_LOCAL",
        default_obs_label="annotation", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="Zebrafish VRH", species="斑马鱼",
    ),
    "zesta": AtlasSpec(
        name="zesta", api_prefix="STDS0000057_", cache_env_var="ZESTA_CACHE", use_local_env_var="ZESTA_USE_LOCAL",
        default_obs_label="layer_annotation", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="ZESTA", species="斑马鱼",
    ),
    "cima": AtlasSpec(
        name="cima", api_prefix="CIMA_", cache_env_var="CIMA_CACHE", use_local_env_var="CIMA_USE_LOCAL",
        default_obs_label="cell_type_l4", fuzzy_gene_symbols=False, catalog_list_name="datasets_list.tsv",
        display_name="CIMA (TrueBlood)", species="人",
    ),
    "absna": AtlasSpec(
        name="absna", api_prefix="cdcp_SCDS0000639_", cache_env_var="ABSNA_CACHE", use_local_env_var="ABSNA_USE_LOCAL",
        default_obs_label="cell_type", fuzzy_gene_symbols=True, catalog_list_name="datasets_list.tsv",
        display_name="ABSNA", species="羊膜动物（鳖/雀/鸽/鼠/猕猴）",
    ),
    "scatlashcl": AtlasSpec(
        name="scatlashcl", api_prefix="cdcp_SCDS0000040_", cache_env_var="SCATLASHCL_CACHE",
        use_local_env_var="SCATLASHCL_USE_LOCAL", default_obs_label="cell_type", fuzzy_gene_symbols=False,
        catalog_list_name="datasets_list.tsv", catalog_atlas="SCDS0000040",
        display_name="SCAtlas HCL", species="人",
    ),
}

_current: Optional[str] = None
DEFAULT_OBS_LABEL = "celltype"
_CUSTOM_CATALOG = frozenset({"hesta", "mosta", "mccsta"})
_CUSTOM_ATLASES = _CUSTOM_CATALOG


def _load_stds_meta() -> dict[str, dict]:
    global _stds_meta_cache
    if _stds_meta_cache is not None:
        return _stds_meta_cache
    if os.path.isfile(_STDS_REGISTRY_JSON):
        with open(_STDS_REGISTRY_JSON, encoding="utf-8") as f:
            _stds_meta_cache = json.load(f)
    else:
        _stds_meta_cache = {}
    return _stds_meta_cache


def _normalize_atlas_key(name: str) -> str:
    """Named atlases stay lowercase; portal STDS/SCDS IDs are uppercase."""
    raw = name.strip()
    if _STDS_NAME_RE.match(raw):
        return raw.upper()
    if _SCDS_NAME_RE.match(raw):
        return raw.upper()
    return raw.lower()


def _stds_id_from_name(name: str) -> str:
    u = name.strip().upper()
    return u if u.startswith("STDS") else f"STDS{name[4:].upper()}"


def _scds_id_from_name(name: str) -> str:
    u = name.strip().upper()
    return u if u.startswith("SCDS") else f"SCDS{name[4:].upper()}"


def _load_cdcp_meta() -> dict[str, dict]:
    global _cdcp_meta_cache
    if _cdcp_meta_cache is not None:
        return _cdcp_meta_cache
    if os.path.isfile(_CDCP_REGISTRY_JSON):
        with open(_CDCP_REGISTRY_JSON, encoding="utf-8") as f:
            _cdcp_meta_cache = json.load(f)
    else:
        _cdcp_meta_cache = {}
    return _cdcp_meta_cache


def _load_portal_meta() -> dict[str, dict]:
    global _portal_meta_cache
    if _portal_meta_cache is not None:
        return _portal_meta_cache
    if os.path.isfile(_PORTAL_REGISTRY_JSON):
        with open(_PORTAL_REGISTRY_JSON, encoding="utf-8") as f:
            raw = json.load(f)
        _portal_meta_cache = {
            k: v for k, v in raw.items()
            if not str(k).startswith("_") and isinstance(v, dict)
        }
    else:
        _portal_meta_cache = {}
    return _portal_meta_cache


def _make_portal_spec(name: str, meta: Optional[dict] = None) -> AtlasSpec:
    meta = meta or {}
    key = name.strip().lower()
    return AtlasSpec(
        name=key,
        api_prefix=meta["api_prefix"] if "api_prefix" in meta else f"{key}_",
        cache_env_var=f"{key.upper()}_CACHE",
        use_local_env_var=f"{key.upper()}_USE_LOCAL",
        default_obs_label=meta.get("default_obs") or "clusters",
        fuzzy_gene_symbols=True,
        catalog_list_name="datasets_list.tsv",
        catalog_atlas=key,
        display_name=meta.get("display") or key.upper(),
        species=meta.get("species") or "",
        portal_url=meta.get("portal_url") or "",
        visual_engine=meta.get("visual_engine") or "",
    )


def _make_cdcp_spec(name: str, meta: Optional[dict] = None) -> AtlasSpec:
    scds_id = _scds_id_from_name(name)
    meta = meta or {}
    return AtlasSpec(
        name=name,
        api_prefix=meta.get("api_prefix") or f"{scds_id}_",
        cache_env_var=f"{scds_id}_CACHE",
        use_local_env_var=f"{scds_id}_USE_LOCAL",
        default_obs_label=meta.get("default_obs") or "celltype",
        fuzzy_gene_symbols=True,
        catalog_list_name="datasets_list.tsv",
        display_name=meta.get("display") or scds_id,
        species=meta.get("species") or "",
    )


def _make_stds_spec(name: str, meta: Optional[dict] = None) -> AtlasSpec:
    stds_id = _stds_id_from_name(name)
    meta = meta or {}
    return AtlasSpec(
        name=name,
        api_prefix=meta.get("api_prefix") or f"{stds_id}_",
        cache_env_var=f"{stds_id}_CACHE",
        use_local_env_var=f"{stds_id}_USE_LOCAL",
        default_obs_label=meta.get("default_obs") or "clusters",
        fuzzy_gene_symbols=True,
        catalog_list_name="datasets_list.tsv",
        display_name=meta.get("display") or stds_id,
        species=meta.get("species") or "",
    )


def lookup_atlas(name: str) -> Optional[AtlasSpec]:
    key = _normalize_atlas_key(name)
    if key in ATLASES:
        return ATLASES[key]
    portal = _load_portal_meta()
    if key in portal:
        return _make_portal_spec(key, portal[key])
    if _STDS_NAME_RE.match(key):
        return _make_stds_spec(key, _load_stds_meta().get(key))
    if _SCDS_NAME_RE.match(key):
        return _make_cdcp_spec(key, _load_cdcp_meta().get(key))
    return None


def list_atlas_names() -> list[str]:
    names = set(ATLASES)
    names.update(_load_portal_meta().keys())
    names.update(_load_stds_meta().keys())
    names.update(_load_cdcp_meta().keys())
    return sorted(names)


def datasets_root() -> str:
    return _DATASETS_ROOT


def shared_lib_dir() -> str:
    return os.path.dirname(os.path.abspath(__file__))


def atlas_root(atlas: Optional[str] = None) -> Optional[str]:
    if atlas is None:
        if _current:
            name = _current
        else:
            env = os.environ.get("STOMICS_ATLAS", "").strip().lower()
            name = env if env in ATLASES else ""
    else:
        name = _normalize_atlas_key(atlas) if atlas else ""
    if not name or lookup_atlas(name) is None:
        return None
    custom = os.path.join(_DATASETS_ROOT, "custom", name)
    if os.path.isdir(custom):
        return custom
    return None


def atlas_lib_dir(atlas: Optional[str] = None) -> Optional[str]:
    root = atlas_root(atlas)
    if not root:
        return None
    lib = os.path.join(root, "lib", "scripts")
    return lib if os.path.isdir(lib) else None


def shared_root() -> str:
    return os.path.join(_DATASETS_ROOT, "_shared")


def get_atlas() -> AtlasSpec:
    if _current is None:
        env = os.environ.get("STOMICS_ATLAS", "").strip().lower()
        if lookup_atlas(env):
            set_atlas(env)
        else:
            raise RuntimeError(
                "Atlas not set. Run via datasets/run.py --atlas <name> or set STOMICS_ATLAS. "
                f"Named atlases: {', '.join(sorted(ATLASES))}; "
                f"or STDS* from stds_registry.json ({len(_load_stds_meta())} registered); "
                f"or SCDS* from cdcp_registry.json ({len(_load_cdcp_meta())} registered)"
            )
    spec = lookup_atlas(_current)
    if spec is None:
        raise RuntimeError(f"Atlas {_current!r} is no longer registered")
    return spec


def set_atlas(name: str) -> AtlasSpec:
    global _current, DEFAULT_OBS_LABEL
    key = _normalize_atlas_key(name)
    spec = lookup_atlas(key)
    if spec is None:
        hint =                 f"Named: {', '.join(sorted(ATLASES))}"
        portal = _load_portal_meta()
        if portal:
            hint += f"; portal atlases: {', '.join(sorted(portal))}"
        if _load_stds_meta():
            hint += f"; STDS* count={len(_load_stds_meta())}"
        if _load_cdcp_meta():
            hint += f"; SCDS* count={len(_load_cdcp_meta())}"
        raise ValueError(f"Unknown atlas {name!r}. {hint}")
    _current = key
    DEFAULT_OBS_LABEL = spec.default_obs_label
    return spec


def detect_atlas_from_path(path: str) -> Optional[str]:
    parts = os.path.normpath(path).split(os.sep)
    if "custom" in parts:
        idx = parts.index("custom")
        if idx + 1 < len(parts):
            candidate = _normalize_atlas_key(parts[idx + 1])
            if lookup_atlas(candidate):
                return candidate
    for name in sorted(list_atlas_names(), key=len, reverse=True):
        if name in parts:
            return name
    return None


def resolve_dataset_ref(data_dir: str):
    import catalog_bridge as cat

    return cat.resolve_dataset_ref(data_dir)


def catalog_path() -> str:
    from catalog_io import default_catalog_path

    return default_catalog_path()


def has_api() -> bool:
    return bool(get_atlas().api_prefix)
