"""Scanpy / integration analysis helpers."""

from __future__ import annotations

from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd


def require_scanpy():
    try:
        import scanpy as sc
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("需要安装 scanpy：pip install scanpy matplotlib seaborn") from exc
    return sc


def run_qc(
    adata: ad.AnnData,
    outdir: Path,
    min_genes: int = 200,
    max_mito: float = 20.0,
) -> tuple[ad.AnnData, dict]:
    sc = require_scanpy()
    sc.settings.figdir = str(outdir / "figures")
    sc.settings.autoshow = False

    adata = adata.copy()
    adata.var["mt"] = adata.var_names.str.upper().str.startswith(("MT-", "MT.", "GENE0"))
    sc.pp.calculate_qc_metrics(adata, qc_vars=["mt"], percent_top=None, log1p=False, inplace=True)

    before = adata.n_obs
    sc.pl.violin(
        adata,
        ["n_genes_by_counts", "total_counts", "pct_counts_mt"],
        jitter=0.3,
        multi_panel=True,
        show=False,
        save="_qc_violin.png",
    )
    adata = adata[adata.obs["n_genes_by_counts"] >= min_genes].copy()
    adata = adata[adata.obs["pct_counts_mt"] <= max_mito].copy()
    after = adata.n_obs
    stats = {
        "n_before": before,
        "n_after": after,
        "min_genes": min_genes,
        "max_mito": max_mito,
        "median_genes": float(np.median(adata.obs["n_genes_by_counts"])) if after else 0,
        "median_counts": float(np.median(adata.obs["total_counts"])) if after else 0,
    }
    adata.obs[["n_genes_by_counts", "total_counts", "pct_counts_mt"]].to_csv(
        outdir / "tables" / "qc_metrics.csv"
    )
    return adata, stats


def run_preprocess(
    adata: ad.AnnData,
    outdir: Path,
    n_top_genes: int = 2000,
    n_pcs: int = 30,
) -> ad.AnnData:
    sc = require_scanpy()
    sc.settings.figdir = str(outdir / "figures")
    sc.settings.autoshow = False
    adata = adata.copy()
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    sc.pp.highly_variable_genes(adata, n_top_genes=min(n_top_genes, adata.n_vars - 1), flavor="seurat")
    adata.raw = adata
    if "highly_variable" in adata.var:
        adata = adata[:, adata.var["highly_variable"]].copy()
    sc.pp.scale(adata, max_value=10)
    sc.tl.pca(adata, n_comps=min(n_pcs, adata.n_vars - 1, adata.n_obs - 1))
    sc.pl.pca_variance_ratio(adata, n_pcs=min(20, adata.obsm["X_pca"].shape[1]), show=False, save="_pca.png")
    hv = int(adata.var["highly_variable"].sum()) if "highly_variable" in adata.var else adata.n_vars
    pd.DataFrame({"n_hvg": [hv], "n_pcs": [adata.obsm["X_pca"].shape[1]]}).to_csv(
        outdir / "tables" / "preprocess_summary.csv", index=False
    )
    return adata


def run_cluster(
    adata: ad.AnnData,
    outdir: Path,
    resolution: float = 0.5,
) -> ad.AnnData:
    sc = require_scanpy()
    sc.settings.figdir = str(outdir / "figures")
    sc.settings.autoshow = False
    adata = adata.copy()
    if "X_pca" not in adata.obsm:
        raise ValueError("缺少 PCA，请先运行 scanpy_preprocess")
    sc.pp.neighbors(adata, n_pcs=min(30, adata.obsm["X_pca"].shape[1]))
    sc.tl.umap(adata)
    sc.tl.leiden(adata, resolution=resolution, flavor="igraph", n_iterations=2, directed=False)
    sc.pl.umap(adata, color=["leiden"], show=False, save="_leiden.png")
    counts = adata.obs["leiden"].value_counts().rename_axis("cluster").reset_index(name="n_cells")
    counts.to_csv(outdir / "tables" / "cluster_sizes.csv", index=False)
    return adata


def run_markers(
    adata: ad.AnnData,
    outdir: Path,
    groupby: str = "leiden",
    n_genes: int = 10,
) -> pd.DataFrame:
    sc = require_scanpy()
    sc.settings.figdir = str(outdir / "figures")
    sc.settings.autoshow = False
    adata = adata.copy()
    if groupby not in adata.obs:
        raise ValueError(f"obs 中无列 {groupby}，请先聚类或指定 --groupby")
    # prefer raw if present for DE
    use = adata.raw.to_adata() if adata.raw is not None else adata
    use.obs[groupby] = adata.obs[groupby].values
    sc.tl.rank_genes_groups(use, groupby=groupby, method="wilcoxon")
    sc.pl.rank_genes_groups(use, n_genes=n_genes, show=False, save="_markers.png")
    frames = []
    for g in use.obs[groupby].astype(str).unique():
        df = sc.get.rank_genes_groups_df(use, group=g).head(n_genes)
        df.insert(0, "cluster", g)
        frames.append(df)
    table = pd.concat(frames, ignore_index=True)
    table.to_csv(outdir / "tables" / "markers.csv", index=False)
    return table


def run_multi_integrate(
    paths: list[str],
    outdir: Path,
    batch_key: str = "batch",
) -> tuple[ad.AnnData, dict]:
    sc = require_scanpy()
    sc.settings.figdir = str(outdir / "figures")
    sc.settings.autoshow = False

    from .io import load_adata

    adatas = []
    for i, p in enumerate(paths):
        a = load_adata(p)
        if batch_key not in a.obs:
            a.obs[batch_key] = f"batch{i}"
        a.obs[batch_key] = a.obs[batch_key].astype(str)
        a.var_names_make_unique()
        adatas.append(a)

    keys = [str(a.obs[batch_key].iloc[0]) for a in adatas]
    adata = ad.concat(adatas, label=batch_key, keys=keys, join="inner", index_unique="-")
    adata.obs_names_make_unique()
    # drop all-zero genes that break HVG binning
    import numpy as _np
    from scipy import sparse as _sp

    X = adata.X
    if _sp.issparse(X):
        keep = _np.asarray(X.sum(axis=0)).ravel() > 0
    else:
        keep = _np.asarray(X).sum(axis=0) > 0
    adata = adata[:, keep].copy()

    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    n_top = min(2000, max(50, adata.n_vars - 1))
    try:
        sc.pp.highly_variable_genes(adata, n_top_genes=n_top, flavor="seurat", batch_key=batch_key)
    except (ValueError, KeyError):
        sc.pp.highly_variable_genes(adata, n_top_genes=n_top, flavor="seurat")
    adata.raw = adata
    if "highly_variable" in adata.var and adata.var["highly_variable"].any():
        adata = adata[:, adata.var["highly_variable"]].copy()
    sc.pp.scale(adata, max_value=10)
    sc.tl.pca(adata, n_comps=min(30, adata.n_vars - 1, adata.n_obs - 1))

    # before
    sc.pp.neighbors(adata, n_pcs=min(20, adata.obsm["X_pca"].shape[1]))
    sc.tl.umap(adata)
    adata.obsm["X_umap_before"] = adata.obsm["X_umap"].copy()
    sc.pl.umap(adata, color=[batch_key], show=False, save="_before_batch.png")

    # Combat batch correction on scaled matrix (light self-built path)
    try:
        sc.pp.combat(adata, key=batch_key)
        method = "combat"
    except Exception:  # noqa: BLE001
        method = "pca_only_no_combat"
    sc.tl.pca(adata, n_comps=min(30, adata.n_vars - 1, adata.n_obs - 1))
    sc.pp.neighbors(adata, n_pcs=min(20, adata.obsm["X_pca"].shape[1]))
    sc.tl.umap(adata)
    sc.pl.umap(adata, color=[batch_key], show=False, save="_after_batch.png")

    mix = _batch_mixing_score(adata.obsm["X_umap"], adata.obs[batch_key].to_numpy())
    stats = {
        "n_datasets": len(paths),
        "n_cells": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "method": method,
        "batch_mixing_knn": mix,
        "batches": sorted(adata.obs[batch_key].unique().tolist()),
    }
    pd.DataFrame([stats]).to_csv(outdir / "tables" / "integration_summary.csv", index=False)
    return adata, stats


def run_scvi_or_fallback(
    adata: ad.AnnData,
    outdir: Path,
    batch_key: str = "batch",
    max_epochs: int = 50,
) -> tuple[ad.AnnData, dict]:
    sc = require_scanpy()
    sc.settings.figdir = str(outdir / "figures")
    sc.settings.autoshow = False
    adata = adata.copy()
    if batch_key not in adata.obs:
        raise ValueError(f"缺少 batch 列：{batch_key}")

    try:
        import scvi
    except ImportError:
        # fallback
        if "X_pca" not in adata.obsm:
            sc.pp.normalize_total(adata, target_sum=1e4)
            sc.pp.log1p(adata)
            n_top = min(2000, max(50, adata.n_vars - 1))
            try:
                sc.pp.highly_variable_genes(adata, n_top_genes=n_top, flavor="seurat", batch_key=batch_key)
            except (ValueError, KeyError):
                sc.pp.highly_variable_genes(adata, n_top_genes=n_top, flavor="seurat")
            if "highly_variable" in adata.var and adata.var["highly_variable"].any():
                adata = adata[:, adata.var["highly_variable"]].copy()
            sc.pp.scale(adata, max_value=10)
            sc.tl.pca(adata)
        try:
            sc.pp.combat(adata, key=batch_key)
            method = "fallback_combat"
        except Exception:  # noqa: BLE001
            method = "fallback_pca"
        sc.tl.pca(adata)
        sc.pp.neighbors(adata)
        sc.tl.umap(adata)
        sc.pl.umap(adata, color=[batch_key], show=False, save="_scvi_fallback.png")
        mix = _batch_mixing_score(adata.obsm["X_umap"], adata.obs[batch_key].to_numpy())
        return adata, {"method": method, "note": "未安装 scvi-tools，已降级 Combat/PCA", "batch_mixing_knn": mix}

    # scVI path — keep counts in layers
    if "counts" not in adata.layers:
        adata.layers["counts"] = adata.X.copy()
    scvi.model.SCVI.setup_anndata(adata, layer="counts", batch_key=batch_key)
    model = scvi.model.SCVI(adata, n_latent=16)
    model.train(max_epochs=max_epochs, early_stopping=True, enable_progress_bar=False)
    adata.obsm["X_scVI"] = model.get_latent_representation()
    sc.pp.neighbors(adata, use_rep="X_scVI")
    sc.tl.umap(adata)
    sc.pl.umap(adata, color=[batch_key], show=False, save="_scvi.png")
    mix = _batch_mixing_score(adata.obsm["X_umap"], adata.obs[batch_key].to_numpy())
    return adata, {"method": "scvi", "batch_mixing_knn": mix, "max_epochs": max_epochs}


def _batch_mixing_score(emb: np.ndarray, batch: np.ndarray, k: int = 30) -> float:
    """Fraction of kNN neighbors from a different batch (higher ≈ better mixing)."""
    from sklearn.neighbors import NearestNeighbors

    k = min(k, len(emb) - 1)
    if k < 2:
        return 0.0
    nn = NearestNeighbors(n_neighbors=k + 1).fit(emb)
    idx = nn.kneighbors(return_distance=False)[:, 1:]
    same = 0
    total = 0
    for i, neigh in enumerate(idx):
        same += np.sum(batch[neigh] == batch[i])
        total += len(neigh)
    # return mixing = 1 - same-batch fraction
    return float(1.0 - same / total) if total else 0.0
