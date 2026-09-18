"""Lazy h5ad I/O for CDCP / FTP-only samples (no Cirrocumulus parquet)."""

from __future__ import annotations

import os
import ssl
import urllib.error
import urllib.request
from typing import Any

import certifi
import numpy as np
from scipy import sparse

_OBS_PRIORITY = (
    "celltype",
    "cell_type",
    "annotation",
    "Annotation",
    "clusters",
    "leiden",
    "louvain",
    "seurat_clusters",
    "Region",
    "region",
)
_EMBEDDING_PRIORITY = (
    ("spatial", ("spatial_1", "spatial_2")),
    ("X_umap", ("UMAP_1", "UMAP_2")),
    ("X_UMAP", ("UMAP_1", "UMAP_2")),
    ("umap", ("UMAP_1", "UMAP_2")),
)


def _download(url: str, dest: str) -> None:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    tmp = dest + ".part"
    if os.path.exists(dest):
        return
    ctx = ssl.create_default_context(cafile=certifi.where())
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, context=ctx, timeout=600) as resp:
            total = int(resp.headers.get("Content-Length") or 0)
            done = 0
            with open(tmp, "wb") as f:
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
            if total and done != total:
                raise OSError(f"Incomplete download: {done}/{total} bytes")
    except urllib.error.HTTPError as e:
        raise FileNotFoundError(f"Failed to download h5ad: HTTP {e.code} ({url})") from e
    except urllib.error.URLError as e:
        raise FileNotFoundError(f"Failed to download h5ad: {e.reason} ({url})") from e
    os.replace(tmp, dest)


class H5adHandle:
    """Backed AnnData with schema-like helpers."""

    def __init__(self, path: str):
        import anndata as ad

        self.path = path
        self._adata = ad.read_h5ad(path, backed="r")

    def close(self) -> None:
        if self._adata is not None:
            self._adata.file.close()
            self._adata = None

    @property
    def adata(self):
        return self._adata

    def shape(self) -> tuple[int, int]:
        return self._adata.n_obs, self._adata.n_vars

    def var_names(self) -> list[str]:
        return list(self._adata.var_names.astype(str))

    def obs_columns(self) -> list[str]:
        return list(self._adata.obs.columns.astype(str))

    def default_obs_column(self) -> str:
        cols = self.obs_columns()
        lower = {c.lower(): c for c in cols}
        for want in _OBS_PRIORITY:
            if want in cols:
                return want
            if want.lower() in lower:
                return lower[want.lower()]
        return cols[0] if cols else "__all__"

    def load_obs(self, column: str) -> np.ndarray:
        cols = self.obs_columns()
        if not cols or column == "__all__":
            return np.array(["cell"] * self._adata.n_obs, dtype=object)
        if column not in cols:
            lower = {c.lower(): c for c in cols}
            column = lower.get(column.lower(), column)
        if column not in self._adata.obs.columns:
            hint = ", ".join(cols[:12]) if cols else "(none — using single group 'cell')"
            raise FileNotFoundError(f"obs column not found: {column!r}. Available: {hint}")
        return np.asarray(self._adata.obs[column].values, dtype=object)

    def _as_sparse_x(self):
        x = self._adata.X
        if hasattr(x, "to_memory"):
            x = x.to_memory()
        if sparse.issparse(x):
            return x
        return sparse.csr_matrix(np.asarray(x))

    def _compute_xy_pca(self, cache_path: str) -> np.ndarray:
        from sklearn.utils.extmath import randomized_svd

        n = self._adata.n_obs
        print(f"Computing 2D PCA embedding for {n:,} cells (one-time, cached) …", flush=True)
        x = self._as_sparse_x()
        u, s, _vt = randomized_svd(x, n_components=2, n_iter=4, random_state=0)
        xy = (u * s).astype(np.float32, copy=False)
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        np.save(cache_path, xy)
        return xy

    def load_xy(self, cache_path: str | None = None) -> np.ndarray:
        key = self.embedding_key()
        if key:
            arr = np.asarray(self._adata.obsm[key])
            if arr.ndim == 2 and arr.shape[1] >= 2:
                return arr[:, :2].astype(np.float32, copy=False)
        if cache_path and os.path.exists(cache_path):
            return np.load(cache_path, mmap_mode="r")
        if cache_path:
            return self._compute_xy_pca(cache_path)
        raise FileNotFoundError(
            "h5ad has no obsm embedding (spatial / X_umap) and no cache path for PCA fallback."
        )

    def embedding_key(self) -> str | None:
        for key, _ in _EMBEDDING_PRIORITY:
            if key in self._adata.obsm:
                return key
        if self._adata.obsm.keys():
            return list(self._adata.obsm.keys())[0]
        return None

    def embedding_axis_labels(self, key: str | None = None) -> tuple[str, str]:
        key = key or self.embedding_key()
        if not key:
            return "PCA_1", "PCA_2"
        for k, labels in _EMBEDDING_PRIORITY:
            if k == key:
                return labels
        return f"{key}_1", f"{key}_2"

    def resolve_gene(self, gene: str, *, fuzzy: bool = True) -> str | None:
        names = self._adata.var_names.astype(str)
        if gene in names:
            return gene
        if not fuzzy:
            return None
        index = {n.lower(): n for n in names}
        for cand in (gene, gene.capitalize(), gene.title(), gene.upper(), gene.lower()):
            hit = index.get(str(cand).lower())
            if hit:
                return hit
        return None

    def load_gene(self, gene: str) -> tuple[np.ndarray, np.ndarray]:
        resolved = self.resolve_gene(gene, fuzzy=True)
        if not resolved:
            raise FileNotFoundError(f"Gene '{gene}' not found in h5ad var.")
        col = self._adata[:, resolved].X
        if sparse.issparse(col):
            col = col.tocoo()
            return col.row.astype(np.int64), col.data.astype(np.float32, copy=False)
        flat = np.asarray(col).reshape(-1)
        idx = np.flatnonzero(flat)
        return idx, flat[idx].astype(np.float32, copy=False)

    def pseudo_schema(self) -> dict[str, Any]:
        obs_cols = self.obs_columns()
        default_obs = self.default_obs_column()
        colors = {default_obs: {}}
        for cat in sorted(set(map(str, self.load_obs(default_obs)))):
            colors[default_obs][cat] = "#888888"
        return {
            "shape": list(self.shape()),
            "var": self.var_names(),
            "obsCat": obs_cols,
            "colors": colors,
            "markers": [],
            "embeddings": [{"name": self.embedding_key() or "X_umap"}],
            "backend": "h5ad",
        }


def ensure_h5ad(local_path: str, download_url: str) -> str:
    if not os.path.isfile(local_path):
        if not download_url:
            raise FileNotFoundError(f"Missing h5ad and no download URL: {local_path}")
        print(f"Downloading h5ad ({download_url}) …", flush=True)
        _download(download_url, local_path)
    return local_path
