"""AnnData I/O and demo dataset builders."""

from __future__ import annotations

from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse


def load_adata(path: str | Path) -> ad.AnnData:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"输入不存在：{path}")
    if path.is_dir():
        # try Visium-style first, then 10x mtx
        try:
            import scanpy as sc

            return sc.read_visium(path.as_posix())
        except Exception:
            pass
        try:
            import scanpy as sc

            return sc.read_10x_mtx(path.as_posix(), var_names="gene_symbols", cache=False)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"无法作为 Visium/10x 目录读取：{path} ({exc})") from exc
    suffix = path.suffix.lower()
    if suffix == ".h5ad":
        return ad.read_h5ad(path)
    if suffix in {".h5", ".hdf5"}:
        import scanpy as sc

        try:
            return sc.read_10x_h5(path.as_posix())
        except Exception:
            return sc.read_h5ad(path.as_posix())
    raise ValueError(f"不支持的输入格式：{path}（支持 h5ad / Visium 目录 / 10x h5 / 10x mtx）")


def save_adata(adata: ad.AnnData, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(path)
    return path


def read_spatial_io(
    path: str | Path,
    platform: str = "auto",
) -> tuple[ad.AnnData, str]:
    """Load multi-platform spatial data into AnnData with obsm['spatial'].

    platform: auto | h5ad | visium | 10x_mtx | 10x_h5
    Returns (adata, resolved_platform).
    """
    path = Path(path)
    platform = (platform or "auto").lower()

    def _ensure_spatial(a: ad.AnnData) -> ad.AnnData:
        if "spatial" in a.obsm:
            return a
        # Visium often stores coords in uns; try scanpy convention
        if "spatial" in a.uns:
            # pick first library
            for lib, meta in a.uns["spatial"].items():
                # coordinates may already be in obsm after read_visium
                break
        raise ValueError(
            "读入后缺少 obsm['spatial']。请用 Visium 目录、含坐标的 h5ad，或先跑 spatial-ingest demo。"
        )

    if platform == "auto":
        if path.is_dir():
            # prefer visium
            try:
                import scanpy as sc

                a = sc.read_visium(path.as_posix())
                a.var_names_make_unique()
                if "spatial" not in a.obsm and hasattr(a, "obsm"):
                    pass
                return _ensure_spatial(a), "visium"
            except Exception:
                a = load_adata(path)
                return _ensure_spatial(a), "10x_mtx"
        if path.suffix.lower() == ".h5ad":
            a = ad.read_h5ad(path)
            return _ensure_spatial(a), "h5ad"
        a = load_adata(path)
        return _ensure_spatial(a), path.suffix.lower().lstrip(".") or "unknown"

    if platform == "h5ad":
        a = ad.read_h5ad(path)
        return _ensure_spatial(a), "h5ad"
    if platform == "visium":
        import scanpy as sc

        a = sc.read_visium(path.as_posix())
        a.var_names_make_unique()
        return _ensure_spatial(a), "visium"
    if platform in {"10x_mtx", "10x_h5", "10x"}:
        a = load_adata(path)
        # synthetic grid if no spatial (capture-less matrix)
        if "spatial" not in a.obsm:
            n = a.n_obs
            g = int(np.ceil(np.sqrt(n)))
            a.obsm["spatial"] = np.array([[i % g, i // g] for i in range(n)], dtype=float)
            return a, platform + "+grid_coords"
        return a, platform

    raise ValueError(f"未知 platform：{platform}")


def make_demo_scrna(
    n_obs: int = 600,
    n_vars: int = 200,
    n_batches: int = 2,
    seed: int = 0,
) -> ad.AnnData:
    """Synthetic scRNA-like counts with batch + celltype structure."""
    rng = np.random.default_rng(seed)
    batch = rng.integers(0, n_batches, size=n_obs)
    celltype = rng.integers(0, 4, size=n_obs)
    base = rng.negative_binomial(5, 0.3, size=(4, n_vars)) + 1
    X = np.zeros((n_obs, n_vars), dtype=np.float32)
    for i in range(n_obs):
        lam = base[celltype[i]] * (1.0 + 0.35 * batch[i])
        X[i] = rng.poisson(lam)
    var = pd.DataFrame(index=[f"GENE{i}" for i in range(n_vars)])
    var["mt"] = [g.startswith("GENE0") for g in var.index]
    obs = pd.DataFrame(
        {
            "batch": [f"batch{b}" for b in batch],
            "celltype": [f"type{c}" for c in celltype],
        }
    )
    adata = ad.AnnData(X=sparse.csr_matrix(X), obs=obs, var=var)
    adata.var_names_make_unique()
    return adata


def make_demo_spatial(
    n_obs: int = 400,
    n_vars: int = 120,
    grid: int = 20,
    seed: int = 1,
) -> ad.AnnData:
    """Synthetic Visium-like spots with spatial coordinates and domains."""
    rng = np.random.default_rng(seed)
    coords = np.array([[i % grid, i // grid] for i in range(n_obs)], dtype=float)
    domain = (coords[:, 0] + coords[:, 1] > grid).astype(int)
    base = rng.negative_binomial(4, 0.35, size=(2, n_vars)) + 1
    base[0, :8] *= 4
    base[1, 8:16] *= 4
    X = np.zeros((n_obs, n_vars), dtype=np.float32)
    for i in range(n_obs):
        X[i] = rng.poisson(base[domain[i]])
    adata = ad.AnnData(
        X=sparse.csr_matrix(X),
        obs=pd.DataFrame({"domain": [f"domain{d}" for d in domain]}),
        var=pd.DataFrame(index=[f"SGENE{i}" for i in range(n_vars)]),
    )
    adata.obsm["spatial"] = coords
    adata.uns["spatial"] = {"demo": {"images": {}, "scalefactors": {"tissue_hires_scalef": 1.0}}}
    return adata


def make_demo_spatial_slices(
    n_slices: int = 2,
    n_obs: int = 300,
    n_vars: int = 100,
    grid: int = 15,
    seed: int = 2,
) -> list[ad.AnnData]:
    """Several spatial slices with shared biology but shifted coordinates + batch effect."""
    rng = np.random.default_rng(seed)
    slices = []
    for s in range(n_slices):
        a = make_demo_spatial(n_obs=n_obs, n_vars=n_vars, grid=grid, seed=seed + s)
        # shift coords and add mild batch effect
        coords = np.asarray(a.obsm["spatial"], dtype=float)
        angle = 0.15 * s
        R = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
        coords = coords @ R.T + np.array([s * (grid + 3), s * 2.0])
        a.obsm["spatial"] = coords
        a.obs["slice"] = f"slice{s}"
        a.obs["batch"] = f"slice{s}"
        X = a.X.toarray() if sparse.issparse(a.X) else np.asarray(a.X, dtype=float)
        X = X * (1.0 + 0.25 * s)
        a.X = sparse.csr_matrix(X.astype(np.float32))
        a.obs_names = [f"slice{s}_{x}" for x in a.obs_names]
        slices.append(a)
    return slices


def split_demo_batches(adata: ad.AnnData) -> list[ad.AnnData]:
    if "batch" not in adata.obs:
        raise ValueError("demo 缺少 batch 列")
    out = []
    for b, idx in adata.obs.groupby("batch").indices.items():
        sub = adata[idx].copy()
        sub.obs["batch"] = b
        out.append(sub)
    return out
