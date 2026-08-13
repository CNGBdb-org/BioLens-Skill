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


def run_spatial_domains(
    adata: ad.AnnData,
    outdir: Path,
    n_domains: int = 4,
    key: str = "domain",
    spatial_weight: float = 0.3,
) -> ad.AnnData:
    """Tissue domains via expression PCA + spatial coords (Leiden if available else KMeans)."""
    sc = require_scanpy()
    sc.settings.figdir = str(outdir / "figures")
    sc.settings.autoshow = False
    adata = adata.copy()
    coords = ensure_spatial(adata)

    sc.pp.calculate_qc_metrics(adata, percent_top=None, log1p=False, inplace=True)
    if "counts" not in adata.layers and adata.X is not None:
        pass
    adata_pp = adata.copy()
    sc.pp.normalize_total(adata_pp, target_sum=1e4)
    sc.pp.log1p(adata_pp)
    n_top = min(1000, max(30, adata_pp.n_vars - 1))
    sc.pp.highly_variable_genes(adata_pp, n_top_genes=n_top, flavor="seurat")
    if "highly_variable" in adata_pp.var and adata_pp.var["highly_variable"].any():
        adata_pp = adata_pp[:, adata_pp.var["highly_variable"]].copy()
    sc.pp.scale(adata_pp, max_value=10)
    n_comps = min(20, adata_pp.n_obs - 1, adata_pp.n_vars - 1)
    sc.tl.pca(adata_pp, n_comps=n_comps)
    pca = np.asarray(adata_pp.obsm["X_pca"], dtype=float)
    # blend spatial into feature space for domain coherence
    c = (coords - coords.mean(0)) / (coords.std(0) + 1e-8)
    feat = np.hstack([pca, spatial_weight * c])

    method = "kmeans"
    try:
        sc.pp.neighbors(adata_pp, use_rep="X_pca", n_neighbors=min(15, adata_pp.n_obs - 1))
        # inject spatial into connectivities lightly via coord knn blend is complex; use Leiden on PCA then
        sc.tl.leiden(adata_pp, resolution=max(0.2, n_domains / 8), key_added=key)
        # if too many/few clusters, fall through to kmeans
        n_found = adata_pp.obs[key].nunique()
        if abs(n_found - n_domains) <= max(2, n_domains // 2):
            adata.obs[key] = adata_pp.obs[key].astype(str).values
            method = f"leiden_res(n={n_found})"
        else:
            raise RuntimeError("leiden k mismatch")
    except Exception:  # noqa: BLE001
        from sklearn.cluster import KMeans

        lab = KMeans(n_clusters=n_domains, n_init=10, random_state=0).fit_predict(feat)
        adata.obs[key] = [f"domain{x}" for x in lab]
        method = f"kmeans_pca+spatial(w={spatial_weight})"

    import matplotlib.pyplot as plt

    cats = sorted(adata.obs[key].astype(str).unique())
    cmap = plt.get_cmap("tab10")
    fig, ax = plt.subplots(figsize=(4.5, 4))
    for i, cat in enumerate(cats):
        m = adata.obs[key].astype(str).to_numpy() == cat
        ax.scatter(coords[m, 0], coords[m, 1], s=10, color=cmap(i % 10), label=cat)
    ax.set_aspect("equal")
    ax.set_title(f"spatial domains ({method})")
    ax.legend(markerscale=1.5, fontsize=7, loc="best")
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "spatial_domains.png", dpi=140)
    plt.close(fig)

    adata.obs[[key]].to_csv(outdir / "tables" / "domain_labels.csv")
    pd.DataFrame(
        {"n_domains": [adata.obs[key].nunique()], "method": [method], "key": [key]}
    ).to_csv(outdir / "tables" / "domains_summary.csv", index=False)
    adata.uns["spatial_domains"] = {"method": method, "key": key}
    return adata


def run_spatial_register(
    adatas: list[ad.AnnData],
    outdir: Path,
    slice_key: str = "slice",
) -> ad.AnnData:
    """Align multiple slices into a common coordinate frame (Procrustes; PASTE optional)."""
    if len(adatas) < 2:
        raise ValueError("spatial-register 需要至少 2 个切片 AnnData")

    aligned = []
    method = "procrustes_expression_landmarks"
    ref = adatas[0].copy()
    if slice_key not in ref.obs:
        ref.obs[slice_key] = "slice0"
    ref_coords = ensure_spatial(ref).copy()
    ref.obsm["spatial"] = ref_coords
    ref.obsm["spatial_raw"] = ref_coords.copy()
    aligned.append(ref)

    # landmark: top variable genes mean expression → soft correspondence via PCA knn
    def _pca_emb(a: ad.AnnData, n_comps: int = 10) -> np.ndarray:
        sc = require_scanpy()
        b = a.copy()
        sc.pp.normalize_total(b, target_sum=1e4)
        sc.pp.log1p(b)
        sc.tl.pca(b, n_comps=min(n_comps, b.n_obs - 1, b.n_vars - 1))
        return np.asarray(b.obsm["X_pca"], dtype=float)

    try:
        # optional PASTE
        import paste  # type: ignore  # noqa: F401

        method = "paste_unavailable_fallback"  # paste API varies; keep fallback primary
    except Exception:  # noqa: BLE001
        pass

    from sklearn.neighbors import NearestNeighbors

    ref_emb = _pca_emb(ref)
    for i, other in enumerate(adatas[1:], start=1):
        o = other.copy()
        if slice_key not in o.obs:
            o.obs[slice_key] = f"slice{i}"
        o_coords = ensure_spatial(o).copy()
        o.obsm["spatial_raw"] = o_coords.copy()
        o_emb = _pca_emb(o)
        # match each query point to nearest ref in expression PCA
        nn = NearestNeighbors(n_neighbors=1).fit(ref_emb)
        idx = nn.kneighbors(o_emb, return_distance=False)[:, 0]
        src = o_coords
        dst = ref_coords[idx]
        # Kabsch / Procrustes
        mu_s, mu_d = src.mean(0), dst.mean(0)
        X = src - mu_s
        Y = dst - mu_d
        U, _, Vt = np.linalg.svd(X.T @ Y)
        R = Vt.T @ U.T
        if np.linalg.det(R) < 0:
            Vt[-1, :] *= -1
            R = Vt.T @ U.T
        aligned_coords = (src - mu_s) @ R + mu_d
        o.obsm["spatial"] = aligned_coords
        aligned.append(o)

    out = ad.concat(aligned, join="inner", index_unique="-")
    out.obs_names_make_unique()
    coords = np.asarray(out.obsm["spatial"], dtype=float)

    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for ax, key, title in [
        (axes[0], "spatial_raw", "before"),
        (axes[1], "spatial", "after register"),
    ]:
        if key not in out.obsm:
            continue
        xy = np.asarray(out.obsm[key], dtype=float)
        for s, sub in out.obs.groupby(slice_key):
            m = out.obs_names.isin(sub.index)
            ax.scatter(xy[m, 0], xy[m, 1], s=6, label=str(s), alpha=0.7)
        ax.set_aspect("equal")
        ax.set_title(title)
        ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "spatial_register.png", dpi=140)
    plt.close(fig)

    pd.DataFrame(
        {
            "n_slices": [len(adatas)],
            "n_spots": [out.n_obs],
            "method": [method],
        }
    ).to_csv(outdir / "tables" / "register_summary.csv", index=False)
    out.uns["spatial_register"] = {"method": method}
    return out


def run_spatial_integrate(
    adata: ad.AnnData,
    outdir: Path,
    batch_key: str = "batch",
) -> tuple[ad.AnnData, dict]:
    """Multi-sample spatial integration (Harmony if present else Combat/PCA)."""
    sc = require_scanpy()
    sc.settings.figdir = str(outdir / "figures")
    sc.settings.autoshow = False
    adata = adata.copy()
    ensure_spatial(adata)
    if batch_key not in adata.obs:
        if "slice" in adata.obs:
            batch_key = "slice"
        else:
            raise ValueError(f"缺少 batch 列：{batch_key}（或 slice）")

    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    n_top = min(1500, max(50, adata.n_vars - 1))
    try:
        sc.pp.highly_variable_genes(adata, n_top_genes=n_top, flavor="seurat", batch_key=batch_key)
    except Exception:  # noqa: BLE001
        sc.pp.highly_variable_genes(adata, n_top_genes=n_top, flavor="seurat")
    if "highly_variable" in adata.var and adata.var["highly_variable"].any():
        adata = adata[:, adata.var["highly_variable"]].copy()
    sc.pp.scale(adata, max_value=10)
    sc.tl.pca(adata, n_comps=min(30, adata.n_vars - 1, adata.n_obs - 1))

    method = "pca_only"
    try:
        import harmonypy as hm

        ho = hm.run_harmony(adata.obsm["X_pca"], adata.obs, batch_key)
        adata.obsm["X_pca_harmony"] = np.asarray(ho.Z_corr).T
        use_rep = "X_pca_harmony"
        method = "harmony"
    except Exception:  # noqa: BLE001
        try:
            sc.pp.combat(adata, key=batch_key)
            sc.tl.pca(adata, n_comps=min(30, adata.n_vars - 1, adata.n_obs - 1))
            method = "combat"
        except Exception:  # noqa: BLE001
            method = "pca_only"
        use_rep = "X_pca"

    sc.pp.neighbors(adata, use_rep=use_rep, n_neighbors=min(15, adata.n_obs - 1))
    sc.tl.umap(adata)

    import matplotlib.pyplot as plt

    coords = ensure_spatial(adata)
    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    for s, sub in adata.obs.groupby(batch_key):
        m = adata.obs_names.isin(sub.index)
        axes[0].scatter(coords[m, 0], coords[m, 1], s=6, label=str(s), alpha=0.7)
    axes[0].set_aspect("equal")
    axes[0].set_title("spatial")
    axes[0].legend(fontsize=7)
    um = np.asarray(adata.obsm["X_umap"])
    for s, sub in adata.obs.groupby(batch_key):
        m = adata.obs_names.isin(sub.index)
        axes[1].scatter(um[m, 0], um[m, 1], s=6, label=str(s), alpha=0.7)
    axes[1].set_title(f"UMAP ({method})")
    axes[1].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "spatial_integrate.png", dpi=140)
    plt.close(fig)

    stats = {
        "n_spots": int(adata.n_obs),
        "n_genes": int(adata.n_vars),
        "method": method,
        "batch_key": batch_key,
        "batches": sorted(adata.obs[batch_key].astype(str).unique().tolist()),
    }
    pd.DataFrame([stats]).to_csv(outdir / "tables" / "integrate_summary.csv", index=False)
    adata.uns["spatial_integrate"] = stats
    return adata, stats


def run_spatial_annotate(
    adata: ad.AnnData,
    outdir: Path,
    marker_csv: str | Path | None = None,
    label_key: str = "cell_type",
    n_clusters: int = 4,
) -> ad.AnnData:
    """Annotate spots/cells: marker scoring if CSV given, else Leiden/KMeans cluster labels."""
    sc = require_scanpy()
    sc.settings.figdir = str(outdir / "figures")
    sc.settings.autoshow = False
    adata = adata.copy()
    coords = ensure_spatial(adata)

    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    method = "cluster_labels"

    if marker_csv:
        mpath = Path(marker_csv)
        mdf = pd.read_csv(mpath)
        # expect columns: gene, cell_type  OR cell_type as columns of genes
        if {"gene", "cell_type"}.issubset(mdf.columns):
            scores = {}
            for ct, g in mdf.groupby("cell_type")["gene"]:
                genes = [x for x in g if x in adata.var_names]
                if not genes:
                    continue
                X = adata[:, genes].X
                vals = np.asarray(X.toarray() if sparse.issparse(X) else X, dtype=float)
                scores[ct] = vals.mean(axis=1)
            if not scores:
                raise ValueError("marker CSV 中基因均不在数据里")
            score_df = pd.DataFrame(scores, index=adata.obs_names)
            adata.obs[label_key] = score_df.idxmax(axis=1).astype(str)
            score_df.to_csv(outdir / "tables" / "marker_scores.csv")
            method = "marker_score"
        else:
            raise ValueError("marker CSV 需要列 gene, cell_type")
    else:
        adata_pp = adata.copy()
        n_top = min(1000, max(30, adata_pp.n_vars - 1))
        sc.pp.highly_variable_genes(adata_pp, n_top_genes=n_top, flavor="seurat")
        if "highly_variable" in adata_pp.var and adata_pp.var["highly_variable"].any():
            adata_pp = adata_pp[:, adata_pp.var["highly_variable"]].copy()
        sc.pp.scale(adata_pp, max_value=10)
        sc.tl.pca(adata_pp, n_comps=min(20, adata_pp.n_obs - 1, adata_pp.n_vars - 1))
        try:
            sc.pp.neighbors(adata_pp, n_neighbors=min(15, adata_pp.n_obs - 1))
            sc.tl.leiden(adata_pp, resolution=0.5, key_added=label_key)
            adata.obs[label_key] = [f"type_{x}" for x in adata_pp.obs[label_key].astype(str)]
            method = "leiden"
        except Exception:  # noqa: BLE001
            from sklearn.cluster import KMeans

            lab = KMeans(n_clusters=n_clusters, n_init=10, random_state=0).fit_predict(
                adata_pp.obsm["X_pca"]
            )
            adata.obs[label_key] = [f"type_{x}" for x in lab]
            method = "kmeans"

    import matplotlib.pyplot as plt

    cats = sorted(adata.obs[label_key].astype(str).unique())
    cmap = plt.get_cmap("tab10")
    fig, ax = plt.subplots(figsize=(4.5, 4))
    for i, cat in enumerate(cats):
        m = adata.obs[label_key].astype(str).to_numpy() == cat
        ax.scatter(coords[m, 0], coords[m, 1], s=10, color=cmap(i % 10), label=cat)
    ax.set_aspect("equal")
    ax.set_title(f"annotation ({method})")
    ax.legend(fontsize=7, loc="best")
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "spatial_annotate.png", dpi=140)
    plt.close(fig)

    adata.obs[[label_key]].value_counts().rename_axis(label_key).reset_index(name="n").to_csv(
        outdir / "tables" / "annotation_counts.csv", index=False
    )
    adata.obs[[label_key]].to_csv(outdir / "tables" / "annotation_labels.csv")
    adata.uns["spatial_annotate"] = {"method": method, "label_key": label_key}
    return adata


def run_spatial_trajectory(
    adata: ad.AnnData,
    outdir: Path,
    root: str | None = None,
    dpt_key: str = "dpt_pseudotime",
) -> ad.AnnData:
    """Diffusion pseudotime on spatial data; color spots by trajectory."""
    sc = require_scanpy()
    sc.settings.figdir = str(outdir / "figures")
    sc.settings.autoshow = False
    adata = adata.copy()
    coords = ensure_spatial(adata)

    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    n_top = min(1000, max(30, adata.n_vars - 1))
    sc.pp.highly_variable_genes(adata, n_top_genes=n_top, flavor="seurat")
    if "highly_variable" in adata.var and adata.var["highly_variable"].any():
        adata = adata[:, adata.var["highly_variable"]].copy()
    sc.pp.scale(adata, max_value=10)
    sc.tl.pca(adata, n_comps=min(20, adata.n_obs - 1, adata.n_vars - 1))
    sc.pp.neighbors(adata, n_neighbors=min(15, adata.n_obs - 1))
    sc.tl.diffmap(adata)

    if root and root in adata.obs_names:
        root_idx = int(np.where(adata.obs_names == root)[0][0])
    else:
        # pick extreme along DC1 / spatial x as root
        root_idx = int(np.argmin(coords[:, 0]))
        root = str(adata.obs_names[root_idx])

    adata.uns["iroot"] = root_idx
    method = "dpt"
    try:
        sc.tl.dpt(adata)
        pt = np.asarray(adata.obs["dpt_pseudotime"], dtype=float)
    except Exception as exc:  # noqa: BLE001
        # fallback: distance along principal curve = PC1 rank
        method = f"pca_rank_fallback({exc.__class__.__name__})"
        pt = np.argsort(np.argsort(adata.obsm["X_pca"][:, 0].astype(float))).astype(float)
        pt = pt / (pt.max() + 1e-8)
        adata.obs[dpt_key] = pt
    else:
        adata.obs[dpt_key] = pt

    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    sc0 = axes[0].scatter(coords[:, 0], coords[:, 1], c=pt, s=10, cmap="viridis")
    axes[0].scatter(coords[root_idx, 0], coords[root_idx, 1], c="red", s=40, marker="*", label="root")
    axes[0].set_aspect("equal")
    axes[0].set_title(f"spatial pseudotime ({method})")
    axes[0].legend(fontsize=7)
    fig.colorbar(sc0, ax=axes[0], fraction=0.046)
    um_ok = False
    try:
        sc.tl.umap(adata)
        um = np.asarray(adata.obsm["X_umap"])
        sc1 = axes[1].scatter(um[:, 0], um[:, 1], c=pt, s=10, cmap="viridis")
        axes[1].set_title("UMAP colored by pseudotime")
        fig.colorbar(sc1, ax=axes[1], fraction=0.046)
        um_ok = True
    except Exception:  # noqa: BLE001
        axes[1].text(0.5, 0.5, "UMAP skipped", ha="center")
    fig.tight_layout()
    fig.savefig(outdir / "figures" / "spatial_trajectory.png", dpi=140)
    plt.close(fig)

    pd.DataFrame({dpt_key: pt}, index=adata.obs_names).to_csv(
        outdir / "tables" / "pseudotime.csv"
    )
    pd.DataFrame(
        {"root": [root], "method": [method], "n_spots": [adata.n_obs], "umap": [um_ok]}
    ).to_csv(outdir / "tables" / "trajectory_summary.csv", index=False)
    adata.uns["spatial_trajectory"] = {"root": root, "method": method}
    return adata
