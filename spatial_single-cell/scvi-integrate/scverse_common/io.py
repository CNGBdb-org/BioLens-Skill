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
        # 10x mtx directory
        try:
            import scanpy as sc

            return sc.read_10x_mtx(path.as_posix(), var_names="gene_symbols", cache=False)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"无法作为 10x 目录读取：{path} ({exc})") from exc
    suffix = path.suffix.lower()
    if suffix == ".h5ad":
        return ad.read_h5ad(path)
    if suffix in {".h5", ".hdf5"}:
        import scanpy as sc

        try:
            return sc.read_10x_h5(path.as_posix())
        except Exception:
            return sc.read_h5ad(path.as_posix())
    raise ValueError(f"不支持的输入格式：{path}（支持 h5ad / 10x h5 / 10x mtx 目录）")


def save_adata(adata: ad.AnnData, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    adata.write_h5ad(path)
    return path


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
    # base expression by celltype
    base = rng.negative_binomial(5, 0.3, size=(4, n_vars)) + 1
    X = np.zeros((n_obs, n_vars), dtype=np.float32)
    for i in range(n_obs):
        lam = base[celltype[i]] * (1.0 + 0.35 * batch[i])
        X[i] = rng.poisson(lam)
    var = pd.DataFrame(index=[f"GENE{i}" for i in range(n_vars)])
    var["mt"] = [g.startswith("GENE0") for g in var.index]  # pretend first genes are MT
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
    # 2 spatial domains
    domain = (coords[:, 0] + coords[:, 1] > grid).astype(int)
    base = rng.negative_binomial(4, 0.35, size=(2, n_vars)) + 1
    # make first 8 genes spatially variable
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


def split_demo_batches(adata: ad.AnnData) -> list[ad.AnnData]:
    """Split demo object into per-batch AnnData list for multi-integrate demos."""
    if "batch" not in adata.obs:
        raise ValueError("demo 缺少 batch 列")
    out = []
    for b, idx in adata.obs.groupby("batch").indices.items():
        sub = adata[idx].copy()
        sub.obs["batch"] = b
        out.append(sub)
    return out
