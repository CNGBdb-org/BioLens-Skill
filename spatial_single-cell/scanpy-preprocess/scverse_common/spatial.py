"""Spatial analysis helpers (Squidpy optional; NumPy/sklearn fallback)."""

from __future__ import annotations

from pathlib import Path

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse


def require_scanpy():
    import scanpy as sc

    return sc


def ensure_spatial(adata: ad.AnnData) -> np.ndarray:
    if "spatial" not in adata.obsm:
        raise ValueError("缺少 obsm['spatial']，请先用 spatial_ingest 读入空间数据")
    return np.asarray(adata.obsm["spatial"], dtype=float)


def run_spatial_qc(adata: ad.AnnData, outdir: Path) -> dict:
    sc = require_scanpy()
    sc.settings.figdir = str(outdir / "figures")
    sc.settings.autoshow = False
    adata = adata.copy()
    coords = ensure_spatial(adata)
    sc.pp.calculate_qc_metrics(adata, percent_top=None, log1p=False, inplace=True)
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(8, 3.5))
    sc1 = axes[0].scatter(coords[:, 0], coords[:, 1], c=adata.obs["total_counts"], s=8, cmap="viridis")
    axes[0].set_title("total_counts")
    axes[0].set_aspect("equal")
    fig.colorbar(sc1, ax=axes[0], fraction=0.046)
    sc2 = axes[1].scatter(coords[:, 0], coords[:, 1], c=adata.obs["n_genes_by_counts"], s=8, cmap="magma")
    axes[1].set_title("n_genes")
    axes[1].set_aspect("equal")
    fig.colorbar(sc2, ax=axes[1], fraction=0.046)
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "spatial_qc.png", dpi=140)
    plt.close(fig)
    stats = {
        "n_spots": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "median_counts": float(np.median(adata.obs["total_counts"])),
        "median_genes": float(np.median(adata.obs["n_genes_by_counts"])),
    }
    pd.DataFrame([stats]).to_csv(outdir / "tables" / "spatial_qc.csv", index=False)
    return stats


def run_spatial_svg(adata: ad.AnnData, outdir: Path, top_n: int = 20) -> pd.DataFrame:
    """Moran's I style spatial autocorrelation; Squidpy if present else DIY."""
    coords = ensure_spatial(adata)
    adata = adata.copy()
    X = adata.X.toarray() if sparse.issparse(adata.X) else np.asarray(adata.X)
    # log1p for stability
    X = np.log1p(X)

    try:
        import squidpy as sq

        sq.gr.spatial_neighbors(adata, coord_type="generic")
        sq.gr.spatial_autocorr(adata, mode="moran", n_jobs=1)
        table = adata.uns["moranI"].copy()
        table = table.sort_values("I", ascending=False).head(top_n)
        table.to_csv(outdir / "tables" / "spatial_variable_genes.csv")
        method = "squidpy_moran"
    except Exception:  # noqa: BLE001
        # DIY: kNN weights Moran's I
        from sklearn.neighbors import NearestNeighbors

        k = min(8, adata.n_obs - 1)
        nn = NearestNeighbors(n_neighbors=k + 1).fit(coords)
        idx = nn.kneighbors(return_distance=False)[:, 1:]
        rows = []
        for g in range(X.shape[1]):
            x = X[:, g]
            z = (x - x.mean()) / (x.std() + 1e-8)
            num = 0.0
            for i, neigh in enumerate(idx):
                num += np.sum(z[i] * z[neigh])
            den = np.sum(z**2) + 1e-8
            I = (adata.n_obs / (k * adata.n_obs)) * (num / den)
            rows.append({"gene": adata.var_names[g], "I": float(I)})
        table = pd.DataFrame(rows).sort_values("I", ascending=False).head(top_n)
        table.to_csv(outdir / "tables" / "spatial_variable_genes.csv", index=False)
        method = "diy_moran_knn"

    # plot top gene
    import matplotlib.pyplot as plt

    top_gene = table.iloc[0]["gene"] if "gene" in table.columns else table.index[0]
    gidx = list(adata.var_names).index(str(top_gene))
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.scatter(coords[:, 0], coords[:, 1], c=X[:, gidx], s=10, cmap="plasma")
    ax.set_title(f"top SVG: {top_gene} ({method})")
    ax.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "top_svg.png", dpi=140)
    plt.close(fig)
    table.attrs = {}  # type: ignore[attr-defined]
    return table


def run_spatial_deconv(
    adata: ad.AnnData,
    outdir: Path,
    n_factors: int = 4,
) -> pd.DataFrame:
    """Baseline NMF deconvolution (spot × factor proportions)."""
    from sklearn.decomposition import NMF

    coords = ensure_spatial(adata)
    X = adata.X.toarray() if sparse.issparse(adata.X) else np.asarray(adata.X, dtype=float)
    X = np.maximum(X, 0)
    n_factors = min(n_factors, X.shape[0] - 1, X.shape[1] - 1)
    model = NMF(n_components=n_factors, init="nndsvda", max_iter=400, random_state=0)
    W = model.fit_transform(X)
    H = model.components_
    prop = W / (W.sum(axis=1, keepdims=True) + 1e-8)
    cols = [f"factor{i}" for i in range(n_factors)]
    prop_df = pd.DataFrame(prop, index=adata.obs_names, columns=cols)
    prop_df.to_csv(outdir / "tables" / "deconv_proportions.csv")
    pd.DataFrame(H, index=cols, columns=adata.var_names).T.to_csv(outdir / "tables" / "deconv_loadings.csv")

    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, n_factors, figsize=(3 * n_factors, 3))
    if n_factors == 1:
        axes = [axes]
    for i, ax in enumerate(axes):
        ax.scatter(coords[:, 0], coords[:, 1], c=prop[:, i], s=8, cmap="Reds")
        ax.set_title(cols[i])
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
    fig.suptitle("NMF deconvolution (baseline)")
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "deconv_factors.png", dpi=140)
    plt.close(fig)
    return prop_df


def run_spatial_interaction(
    adata: ad.AnnData,
    outdir: Path,
    label_key: str = "domain",
    radius: float | None = None,
) -> pd.DataFrame:
    """Neighborhood co-occurrence / enrichment between labels."""
    coords = ensure_spatial(adata)
    if label_key not in adata.obs:
        # invent labels from kmeans if missing
        from sklearn.cluster import KMeans

        labels = KMeans(n_clusters=3, n_init=10, random_state=0).fit_predict(coords)
        adata = adata.copy()
        adata.obs[label_key] = [f"c{x}" for x in labels]

    labels = adata.obs[label_key].astype(str).to_numpy()
    cats = sorted(set(labels))
    from sklearn.neighbors import NearestNeighbors

    if radius is None:
        # use median nearest-neighbor distance * 2.5
        nn1 = NearestNeighbors(n_neighbors=2).fit(coords)
        d, _ = nn1.kneighbors()
        radius = float(np.median(d[:, 1]) * 2.5)

    nn = NearestNeighbors(radius=radius).fit(coords)
    neigh = nn.radius_neighbors(return_distance=False)
    mat = pd.DataFrame(0.0, index=cats, columns=cats)
    for i, nb in enumerate(neigh):
        li = labels[i]
        for j in nb:
            if j == i:
                continue
            mat.loc[li, labels[j]] += 1
    # row-normalize enrichment-ish
    enrich = mat.div(mat.sum(axis=1).replace(0, np.nan), axis=0).fillna(0)
    enrich.to_csv(outdir / "tables" / "spatial_interaction.csv")

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(4, 3.5))
    im = ax.imshow(enrich.to_numpy(), cmap="Blues")
    ax.set_xticks(range(len(cats)))
    ax.set_yticks(range(len(cats)))
    ax.set_xticklabels(cats, rotation=45, ha="right")
    ax.set_yticklabels(cats)
    ax.set_title(f"neighborhood co-occurrence (r={radius:.2f})")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "spatial_interaction.png", dpi=140)
    plt.close(fig)
    return enrich


def plot_spatial_gene(adata: ad.AnnData, gene: str, outdir: Path) -> Path:
    coords = ensure_spatial(adata)
    if gene not in adata.var_names:
        raise ValueError(f"基因不存在：{gene}")
    X = adata[:, gene].X
    vals = np.asarray(X.toarray() if sparse.issparse(X) else X).ravel()
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(4, 4))
    sc = ax.scatter(coords[:, 0], coords[:, 1], c=vals, s=10, cmap="viridis")
    ax.set_title(gene)
    ax.set_aspect("equal")
    fig.colorbar(sc, ax=ax, fraction=0.046)
    fig.tight_layout()
    path = outdir / "figures" / f"gene_{gene}.png"
    fig.savefig(path, dpi=140)
    plt.close(fig)
    return path
