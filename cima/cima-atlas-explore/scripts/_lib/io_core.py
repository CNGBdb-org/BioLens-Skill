"""CNGB Cirrocumulus parquet I/O for HESTA (local cache or Explore API)."""

from __future__ import annotations

import gzip
import io
import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from functools import lru_cache

import certifi
import numpy as np
import pyarrow.parquet as pq

from atlas_registry import get_atlas, resolve_dataset_ref

SPATIAL_CACHE = "spatial_xy.npy"
CNGB_API_BASE = "https://db.cngb.org/stomics/api/explore/api/file"
CNGB_SCHEMA_API = "https://db.cngb.org/stomics/api/explore/api/schema"
ALL_PATH_ENV = "STOMICS_ALL_PATH"
USE_LOCAL_ENV = "STOMICS_USE_LOCAL"


def _validate_parquet_bytes(data: bytes, rel_path: str) -> None:
    if data and data[:4] == b"PAR1":
        return
    preview = data[:120].decode("utf-8", errors="replace").replace("\n", " ")
    raise FileNotFoundError(
        f"Invalid parquet payload for {rel_path} ({len(data)} bytes). Preview: {preview[:80]!r}"
    )


def _cache_root() -> str:
    spec = get_atlas()
    default = os.path.join(os.path.expanduser("~"), ".cache", f"{spec.name}-spatial")
    return os.path.join(os.environ.get(spec.cache_env_var, default))


class Dataset:
    """Local folder or remote CNGB Explore parquet."""

    def __init__(
        self,
        dataset_id,
        *,
        mode,
        local_root=None,
        meta=None,
        explore_id: str | None = None,
    ):
        self.dataset_id = dataset_id
        self.mode = mode
        self.local_root = local_root
        self.meta = meta
        self.explore_id = explore_id or dataset_id
        self._schema = None

    def output_slug(self):
        if self.meta:
            return self.meta.stem
        prefix = get_atlas().api_prefix
        if self.dataset_id.startswith(prefix):
            return self.dataset_id[len(prefix) :]
        return self.dataset_id

    def output_dir(self):
        if self.mode == "local":
            return self.local_root
        out = os.path.join(os.getcwd(), self.output_slug())
        os.makedirs(out, exist_ok=True)
        return out

    def cache_dir(self):
        if self.mode == "local":
            return self.local_root
        path = os.path.join(_cache_root(), self.dataset_id)
        os.makedirs(path, exist_ok=True)
        return path

    def api_url(self, rel_path):
        query = urllib.parse.urlencode({"id": self.explore_id, "file": rel_path})
        return f"{CNGB_API_BASE}?{query}"

    def embedding_axis_labels(self) -> tuple[str, str]:
        return "spatial_1", "spatial_2"

    def _local_path(self, rel_path):
        return os.path.join(self.local_root, rel_path)

    def _cache_path(self, rel_path):
        return os.path.join(self.cache_dir(), rel_path)

    def get_schema(self):
        if self._schema is None:
            self._schema = load_schema(self)
        return self._schema

    def exists(self, rel_path):
        if self.mode == "local":
            return os.path.exists(self._local_path(rel_path))
        if os.path.exists(self._cache_path(rel_path)):
            return True
        url = self.api_url(rel_path)
        try:
            ctx = ssl.create_default_context(cafile=certifi.where())
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                return resp.status == 200
        except urllib.error.HTTPError as e:
            return e.code == 200
        except urllib.error.URLError:
            return False

    def read_bytes(self, rel_path):
        if self.mode == "local":
            path = self._local_path(rel_path)
            if not os.path.exists(path):
                raise FileNotFoundError(f"Missing file: {path}")
            with open(path, "rb") as f:
                data = f.read()
            if rel_path.endswith(".parquet"):
                _validate_parquet_bytes(data, rel_path)
            return data

        cache_path = self._cache_path(rel_path)
        if os.path.exists(cache_path):
            with open(cache_path, "rb") as f:
                data = f.read()
            if rel_path.endswith(".parquet"):
                try:
                    _validate_parquet_bytes(data, rel_path)
                except FileNotFoundError:
                    os.remove(cache_path)
                    if self.mode == "local":
                        raise
                else:
                    return data
            else:
                return data

        url = self.api_url(rel_path)
        try:
            ctx = ssl.create_default_context(cafile=certifi.where())
            with urllib.request.urlopen(url, context=ctx, timeout=120) as resp:
                data = resp.read()
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise FileNotFoundError(f"Remote file not found: {rel_path} ({url})") from e
            raise FileNotFoundError(f"Failed to fetch {rel_path}: HTTP {e.code}") from e
        except urllib.error.URLError as e:
            raise FileNotFoundError(f"Failed to fetch {rel_path}: {e.reason}") from e

        if rel_path.endswith(".parquet"):
            _validate_parquet_bytes(data, rel_path)

        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "wb") as f:
            f.write(data)
        return data

    def read_parquet(self, rel_path, *, columns=None, _retry=True):
        data = self.read_bytes(rel_path)
        try:
            return pq.read_table(io.BytesIO(data), columns=columns)
        except Exception:
            if not _retry or self.mode == "local":
                raise
            cache_path = self._cache_path(rel_path)
            if os.path.exists(cache_path):
                os.remove(cache_path)
                return self.read_parquet(rel_path, columns=columns, _retry=False)
            raise

    def read_parquet_schema(self, rel_path):
        data = self.read_bytes(rel_path)
        return pq.read_schema(io.BytesIO(data))

    def list_genes(self):
        return list(self.get_schema().get("var", []))


def _parquet_explore_available(explore_id: str) -> bool:
    q = urllib.parse.urlencode({"id": explore_id, "file": "index.json.gz"})
    url = f"{CNGB_API_BASE}?{q}"
    try:
        ctx = ssl.create_default_context(cafile=certifi.where())
        req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
            return resp.status == 200
    except urllib.error.HTTPError:
        return False
    except urllib.error.URLError:
        return False


def _global_local_enabled() -> bool:
    return os.environ.get(USE_LOCAL_ENV, "").strip() == "1"


def _atlas_local_enabled(spec) -> bool:
    return os.environ.get(spec.use_local_env_var, "").strip() == "1"


def _local_mode_enabled(spec) -> bool:
    return _global_local_enabled() or _atlas_local_enabled(spec)


def _parse_all_path_lines(text: str) -> dict[str, str]:
    """Parse all_path table: export_id<TAB/space>filesystem_path."""
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        export_id, path = parts[0].strip(), parts[1].strip()
        if export_id and path:
            out[export_id] = path
    return out


@lru_cache(maxsize=2)
def _load_all_path_map(path: str) -> dict[str, str]:
    if not path or not os.path.isfile(path):
        return {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return _parse_all_path_lines(f.read())
    except OSError:
        return {}


def _all_path_map() -> dict[str, str]:
    if not _global_local_enabled():
        return {}
    path = os.environ.get(ALL_PATH_ENV, "").strip()
    if not path:
        return {}
    return _load_all_path_map(os.path.abspath(path))


def _is_parquet_dataset_dir(path: str) -> bool:
    return bool(path) and os.path.isfile(os.path.join(path, "index.json.gz"))


def _local_lookup_keys(data_dir: str, dataset_id: str, explore_id: str, meta, spec) -> list[str]:
    keys: list[str] = []
    seen: set[str] = set()

    def add(key: str) -> None:
        key = (key or "").strip()
        if not key or key in seen:
            return
        seen.add(key)
        keys.append(key)

    add(data_dir)
    add(dataset_id)
    add(explore_id)
    if meta is not None:
        add(getattr(meta, "explore_id", "") or "")
        add(getattr(meta, "stem", "") or "")
        section = getattr(meta, "section", "") or ""
        add(section)
        if section.endswith(".h5ad"):
            add(section[: -len(".h5ad")])

    prefix = spec.api_prefix
    for key in list(keys):
        if prefix and key.startswith(prefix):
            add(key[len(prefix) :])
        add(os.path.basename(key))
    return keys


def _lookup_all_path_root(data_dir: str, dataset_id: str, explore_id: str, meta, spec) -> str | None:
    mapping = _all_path_map()
    if not mapping:
        return None
    for key in _local_lookup_keys(data_dir, dataset_id, explore_id, meta, spec):
        path = mapping.get(key)
        if path and _is_parquet_dataset_dir(path):
            return os.path.abspath(path)
    return None


def _dataset_from_local_dir(local_root: str, dataset_id_hint: str, meta=None) -> Dataset:
    local_root = os.path.abspath(local_root)
    dataset_id = dataset_id_hint
    if meta is None:
        try:
            dataset_id, meta = resolve_dataset_ref(dataset_id_hint)
        except (FileNotFoundError, ValueError):
            meta = None
    return Dataset(dataset_id, mode="local", local_root=local_root, meta=meta)


def resolve_dataset(data_dir):
    spec = get_atlas()
    data_dir = str(data_dir).strip().rstrip("/")
    local = os.path.abspath(data_dir)
    use_local = _local_mode_enabled(spec)
    if use_local and os.path.isdir(local):
        if os.path.exists(os.path.join(local, "index.json.gz")):
            dataset_id = os.path.basename(local.rstrip("/")) or local
            try:
                dataset_id, meta = resolve_dataset_ref(dataset_id)
            except (FileNotFoundError, ValueError):
                meta = None
            return Dataset(dataset_id, mode="local", local_root=local, meta=meta)

    try:
        dataset_id, meta = resolve_dataset_ref(data_dir)
    except FileNotFoundError:
        base = os.path.basename(data_dir)
        dataset_id = data_dir if data_dir.startswith(spec.api_prefix) else f"{spec.api_prefix}{base}"
        meta = None
        local_root = _lookup_all_path_root(data_dir, dataset_id, "", None, spec)
        if local_root:
            return _dataset_from_local_dir(local_root, dataset_id)
    except ValueError:
        raise

    explore_id = getattr(meta, "explore_id", "") if meta else ""

    local_root = _lookup_all_path_root(data_dir, dataset_id, explore_id, meta, spec)
    if local_root:
        return _dataset_from_local_dir(local_root, dataset_id, meta=meta)

    download = getattr(meta, "download", "") if meta else ""
    kind = (getattr(meta, "kind", "") if meta else "").lower()

    if kind in ("cirro_portal", "portal_spa"):
        link = download.replace("portal:", "", 1) if download.startswith("portal:") else ""
        portal = link or get_atlas().portal_url or download
        raise FileNotFoundError(
            f"{dataset_id} 暂无 Explore parquet API（{kind}），请在门户在线检索/可视化：{portal}"
        )

    if explore_id:
        return Dataset(dataset_id, mode="api", meta=meta, explore_id=explore_id)

    # Catalog rows often omit ExploreId but still have a live parquet explore API.
    if _parquet_explore_available(dataset_id):
        return Dataset(dataset_id, mode="api", meta=meta, explore_id=dataset_id)

    if download or kind in ("h5ad", "scrna_h5ad"):
        raise FileNotFoundError(
            f"No Explore parquet API for {dataset_id}. Download URL (manual): {download or 'n/a'}"
        )

    ds = Dataset(
        dataset_id,
        mode="api",
        meta=meta,
        explore_id=explore_id or dataset_id,
    )
    ds.get_schema()
    return ds


def validate_dataset_dir(data_dir):
    return resolve_dataset(data_dir)


def _load_schema_from_remote(explore_id: str) -> dict:
    for file in ("index.json.gz", "index.json"):
        q = urllib.parse.urlencode({"id": explore_id, "file": file})
        url = f"{CNGB_API_BASE}?{q}"
        try:
            ctx = ssl.create_default_context(cafile=certifi.where())
            with urllib.request.urlopen(url, context=ctx, timeout=120) as resp:
                raw = resp.read()
            try:
                payload = gzip.decompress(raw)
            except gzip.BadGzipFile:
                payload = raw
            if isinstance(payload, bytes):
                return json.loads(payload.decode("utf-8"))
            return json.loads(payload)
        except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError, OSError):
            continue
    q = urllib.parse.urlencode({"id": explore_id})
    try:
        ctx = ssl.create_default_context(cafile=certifi.where())
        with urllib.request.urlopen(f"{CNGB_SCHEMA_API}?{q}", context=ctx, timeout=120) as resp:
            return json.loads(resp.read())
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError):
        raise FileNotFoundError(f"Missing explore schema for {explore_id}")


def load_schema(ds):
    if ds.mode == "api" and ds.explore_id:
        cache_path = os.path.join(ds.cache_dir(), "index.json.gz")
        if os.path.exists(cache_path):
            raw = open(cache_path, "rb").read()
            try:
                return json.loads(gzip.decompress(raw))
            except gzip.BadGzipFile:
                return json.loads(raw.decode("utf-8"))
        schema = _load_schema_from_remote(ds.explore_id)
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, "wb") as f:
            f.write(gzip.compress(json.dumps(schema).encode("utf-8")))
        return schema
    raw = ds.read_bytes("index.json.gz")
    try:
        return json.loads(gzip.decompress(raw))
    except gzip.BadGzipFile:
        if isinstance(raw, bytes):
            return json.loads(raw.decode("utf-8"))
        return json.loads(raw)


def list_obs_columns(ds, *, check_exists=False):
    """Candidate obs columns from schema (colors + obsCat)."""
    schema = load_schema(ds)
    cols: list[str] = []
    seen: set[str] = set()
    for key in list(schema.get("colors", {}).keys()) + list(schema.get("obsCat") or []):
        if not isinstance(key, str) or not key.strip() or key in seen:
            continue
        seen.add(key)
        if check_exists and not ds.exists(f"obs/{key}.parquet"):
            continue
        cols.append(key)
    return cols


def resolve_obs_column(ds, column: str | None = None) -> str:
    """Map requested obs name → existing obs/*.parquet (case-insensitive fallback)."""
    spec = get_atlas()
    requested = (column or spec.default_obs_label or "").strip()
    if not requested:
        raise ValueError("No obs column specified and atlas has no default_obs_label")

    candidates: list[str] = []
    for c in (requested, requested.lower(), requested.capitalize(), requested.title(), requested.upper()):
        if c and c not in candidates:
            candidates.append(c)

    schema = load_schema(ds)
    for key in list(schema.get("colors", {}).keys()) + list(schema.get("obsCat") or []):
        if isinstance(key, str) and key not in candidates:
            candidates.append(key)

    lower_to_name = {c.lower(): c for c in candidates}
    for c in candidates:
        rel = f"obs/{c}.parquet"
        if ds.exists(rel):
            return c
        alt = lower_to_name.get(c.lower())
        if alt and alt != c and ds.exists(f"obs/{alt}.parquet"):
            return alt

    available = [c for c in list_obs_columns(ds, check_exists=True)]
    hint = ", ".join(available[:12])
    more = f" ... (+{len(available)-12})" if len(available) > 12 else ""
    raise FileNotFoundError(
        f"obs column not found: {requested!r}. Available: {hint}{more}"
    )


def load_obs_column(ds, column):
    column = resolve_obs_column(ds, column)
    rel = f"obs/{column}.parquet"
    col = ds.read_parquet(rel)["value"]
    if hasattr(col, "to_pylist"):
        return np.array(col.to_pylist(), dtype=object)
    return col.to_numpy()


def load_n_obs(ds):
    return load_schema(ds)["shape"][0]


def _build_spatial_cache(ds, cache_path):
    spatial = ds.read_parquet("obsm/spatial.parquet")
    xy = np.column_stack(
        (spatial["spatial_1"].to_numpy(), spatial["spatial_2"].to_numpy())
    ).astype(np.float32, copy=False)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    np.save(cache_path, xy)


def _embedding_parquet_candidates(ds):
    schema = ds.get_schema()
    names = [e.get("name") for e in (schema.get("embeddings") or []) if e.get("name")]
    priority = ["spatial", "X_umap", "X_tsne", "umap", "tsne"]
    ordered = [n for n in priority if n in names]
    ordered.extend(n for n in names if n not in ordered)
    return [f"obsm/{name}.parquet" for name in ordered]


def _xy_from_obsm_table(table, embedding_name):
    cols = table.column_names
    for c1, c2 in (
        (f"{embedding_name}_1", f"{embedding_name}_2"),
        ("spatial_1", "spatial_2"),
        ("UMAP_1", "UMAP_2"),
        ("TSNE_1", "TSNE_2"),
    ):
        if c1 in cols and c2 in cols:
            return np.column_stack((table[c1].to_numpy(), table[c2].to_numpy())).astype(
                np.float32, copy=False
            )
    if len(cols) >= 2:
        return np.column_stack((table[cols[0]].to_numpy(), table[cols[1]].to_numpy())).astype(
            np.float32, copy=False
        )
    raise ValueError(f"Cannot infer XY columns from {cols}")


def _build_embedding_cache(ds, cache_path, parquet_rel):
    embedding_name = os.path.splitext(os.path.basename(parquet_rel))[0]
    table = ds.read_parquet(parquet_rel)
    xy = _xy_from_obsm_table(table, embedding_name)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    np.save(cache_path, xy)


def load_spatial_xy(ds, use_cache=True):
    parquet_candidates = ["obsm/spatial.parquet"] + [
        p for p in _embedding_parquet_candidates(ds) if p != "obsm/spatial.parquet"
    ]
    parquet_rel = next((p for p in parquet_candidates if ds.exists(p)), None)
    if not parquet_rel:
        raise FileNotFoundError(
            "Missing spatial coordinates: obsm/spatial.parquet or embedding parquet"
        )

    cache_name = SPATIAL_CACHE if parquet_rel == "obsm/spatial.parquet" else f"{os.path.splitext(os.path.basename(parquet_rel))[0]}_xy.npy"
    cache_path = os.path.join(ds.cache_dir(), "obsm", cache_name)
    parquet_path = ds._local_path(parquet_rel) if ds.mode == "local" else ds._cache_path(parquet_rel)

    if use_cache:
        if os.path.exists(cache_path):
            if ds.mode == "local" and os.path.exists(parquet_path):
                if os.path.getmtime(cache_path) >= os.path.getmtime(parquet_path):
                    return np.load(cache_path, mmap_mode="r")
            elif ds.mode == "api":
                return np.load(cache_path, mmap_mode="r")
        if parquet_rel == "obsm/spatial.parquet":
            _build_spatial_cache(ds, cache_path)
        else:
            _build_embedding_cache(ds, cache_path, parquet_rel)
        return np.load(cache_path, mmap_mode="r")

    if parquet_rel == "obsm/spatial.parquet":
        spatial = ds.read_parquet(parquet_rel)
        return np.column_stack(
            (spatial["spatial_1"].to_numpy(), spatial["spatial_2"].to_numpy())
        ).astype(np.float32, copy=False)
    table = ds.read_parquet(parquet_rel)
    return _xy_from_obsm_table(table, os.path.splitext(os.path.basename(parquet_rel))[0])


def _gene_rel_paths(gene):
    escaped = gene.replace(" ", r"\ ") + ".parquet"
    return [
        f"X/{gene}.parquet",
        f"X/{gene.replace(' ', '_')}.parquet",
        f"X/{escaped}",
    ]


def resolve_gene_name(ds, gene):
    var = ds.get_schema().get("var", [])
    if gene in var:
        return gene
    if not get_atlas().fuzzy_gene_symbols:
        return None
    for candidate in (gene.capitalize(), gene.title(), gene.upper(), gene.lower()):
        if candidate in var:
            return candidate
    return None


def resolve_gene_rel(ds, gene):
    resolved = resolve_gene_name(ds, gene)
    if not resolved:
        return None
    gene = resolved
    if gene not in ds.get_schema().get("var", []):
        return None
    for rel in _gene_rel_paths(gene):
        if ds.mode == "local":
            if os.path.exists(ds._local_path(rel)):
                return rel
        else:
            return rel
    return None


def gene_in_var(ds, gene):
    if get_atlas().fuzzy_gene_symbols:
        return resolve_gene_name(ds, gene) is not None
    return gene in ds.get_schema().get("var", [])


def load_gene_sparse(ds, gene):
    rel = resolve_gene_rel(ds, gene)
    if not rel:
        raise FileNotFoundError(
            f"Gene '{gene}' not found under X/. Check symbol or index.json.gz → var."
        )
    t = ds.read_parquet(rel)
    if "index" in t.column_names:
        return t["index"].to_numpy(), t["value"].to_numpy()
    n = load_n_obs(ds)
    return np.arange(n), t["value"].to_numpy()


def gene_dense_vector(ds, gene, n_obs=None):
    if n_obs is None:
        n_obs = load_n_obs(ds)
    idx, val = load_gene_sparse(ds, gene)
    x = np.zeros(n_obs, dtype=np.float32)
    x[idx] = val.astype(np.float32, copy=False)
    return x


def schema_colors(ds, field):
    return load_schema(ds).get("colors", {}).get(field, {})


def list_markers(schema, celltype=None, search=None):
    markers = schema.get("markers", [])
    out = []
    for m in markers:
        name = str(m.get("name", ""))
        if celltype and name.lower() != celltype.lower():
            continue
        feats = m.get("features", [])
        if search:
            feats = [f for f in feats if search.lower() in str(f).lower()]
            if not feats and search.lower() not in name.lower():
                continue
        out.append(
            {
                "category": m.get("category", ""),
                "name": name,
                "features": feats if search else m.get("features", []),
            }
        )
    return out


def setup_matplotlib():
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def sample_name(ds, override=None):
    return override or ds.output_slug()
