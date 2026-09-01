#!/usr/bin/env python3
"""CPU reference → query label transfer (scanpy ingest / KNN).

This is the CIMA-CPU analogue of scVI/scArches mapping: no GPU, no weights.
Shared genes → HVG → joint PCA → kNN majority vote + confidence.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import scanpy as sc

PREFERRED_LABEL_COLS: tuple[str, ...] = (
    "cell_type_l4",
    "cell_type_l3",
    "cell_type_l2",
    "cell_type_l1",
    "final_annotation",
    "celltype_1st",
    "cell_type",
    "annotation",
)


def resolve_reference_label(adata, requested: str | None = None) -> str:
    if requested:
        if requested not in adata.obs.columns:
            raise ValueError(
                f"--reference-label {requested!r} not in reference.obs "
                f"(have: {list(adata.obs.columns)[:20]})"
            )
        return requested
    for col in PREFERRED_LABEL_COLS:
        if col in adata.obs.columns:
            return col
    raise ValueError(
        "Reference has no label column. Pass --reference-label "
        f"(looked for {PREFERRED_LABEL_COLS})."
    )


def _to_array(X):
    if hasattr(X, "toarray"):
        return X.toarray()
    return np.asarray(X)


def _lognorm(ad):
    if "counts" in ad.layers:
        ad.X = ad.layers["counts"].copy()
    sc.pp.normalize_total(ad, target_sum=1e4)
    sc.pp.log1p(ad)
    return ad


def _subsample_ref(ref, label_col: str, max_cells: int, seed: int = 66):
    if ref.n_obs <= max_cells:
        return ref
    rng = np.random.default_rng(seed)
    labels = ref.obs[label_col].astype(str)
    vc = labels.value_counts()
    chosen: list[str] = []
    for lab, n in vc.items():
        take = max(min(n, max(20, int(round(n * max_cells / ref.n_obs)))), 1)
        take = min(take, n)
        idx = labels.index[labels == lab].to_numpy()
        chosen.extend(rng.choice(idx, size=take, replace=False).tolist())
    if len(chosen) > max_cells:
        chosen = rng.choice(chosen, size=max_cells, replace=False).tolist()
    print(f"  Reference subsampled {ref.n_obs} → {len(chosen)} (cap={max_cells})")
    return ref[chosen].copy()


def knn_label_transfer(
    query,
    reference,
    *,
    label_col: str,
    k: int = 15,
    n_pcs: int = 30,
    n_hvg: int = 2000,
    max_ref_cells: int = 20000,
    seed: int = 66,
) -> tuple[list[str], np.ndarray, np.ndarray, dict]:
    """Transfer `label_col` from reference onto query cells.

    Returns (labels, vote_fraction, margin, stats).
    Also writes query.obsm['X_pca'] and query.obsm['X_umap'] from the joint embedding.
    """
    genes = query.var_names.intersection(reference.var_names)
    n_shared = int(len(genes))
    if n_shared < 50:
        raise ValueError(
            f"Too few shared genes between query and reference ({n_shared}). "
            "Need the same gene symbols (e.g. both HGNC)."
        )
    print(f"  Shared genes: {n_shared}")

    q = query[:, genes].copy()
    r = reference[:, genes].copy()
    r = _subsample_ref(r, label_col, max_ref_cells, seed=seed)

    _lognorm(q)
    _lognorm(r)

    batch_key = None
    sc.pp.highly_variable_genes(
        r, n_top_genes=min(n_hvg, r.n_vars), flavor="seurat", batch_key=batch_key
    )
    if "highly_variable" in r.var.columns and int(r.var["highly_variable"].sum()) >= 50:
        hvg = r.var_names[r.var["highly_variable"]]
        q = q[:, hvg].copy()
        r = r[:, hvg].copy()
        print(f"  HVGs from reference: {q.n_vars}")

    r.obs["_xfer_set"] = "ref"
    q.obs["_xfer_set"] = "query"
    r.obs_names = r.obs_names.astype(str) + "-ref"
    q.obs_names = q.obs_names.astype(str) + "-qry"
    try:
        combined = sc.concat([r, q], join="inner", index_unique=None)
    except TypeError:
        combined = r.concatenate(q, join="inner", index_unique=None)

    n_comps = min(n_pcs, combined.n_obs - 1, combined.n_vars - 1)
    sc.tl.pca(combined, n_comps=max(2, n_comps), zero_center=False)
    sc.pp.neighbors(
        combined,
        n_neighbors=min(15, combined.n_obs - 1),
        n_pcs=min(n_pcs, combined.obsm["X_pca"].shape[1]),
        use_rep="X_pca",
    )
    sc.tl.umap(combined, min_dist=0.3)

    n_ref = r.n_obs
    pca = combined.obsm["X_pca"]
    umap = combined.obsm["X_umap"]
    ref_pca = pca[:n_ref]
    qry_pca = pca[n_ref:]
    query.obsm["X_pca"] = np.asarray(qry_pca)
    query.obsm["X_umap"] = np.asarray(umap[n_ref:])

    from sklearn.neighbors import NearestNeighbors

    kk = min(int(k), int(ref_pca.shape[0]))
    nn = NearestNeighbors(n_neighbors=kk, metric="euclidean")
    nn.fit(ref_pca)
    _dist, idx = nn.kneighbors(qry_pca)

    ref_labels = r.obs[label_col].astype(str).to_numpy()
    labels: list[str] = []
    frac = np.zeros(idx.shape[0], dtype=np.float64)
    margin = np.zeros(idx.shape[0], dtype=np.float64)
    for i in range(idx.shape[0]):
        votes = pd.Series(ref_labels[idx[i]]).value_counts()
        labels.append(str(votes.index[0]))
        top = float(votes.iloc[0] / votes.sum())
        second = float(votes.iloc[1] / votes.sum()) if len(votes) > 1 else 0.0
        frac[i] = top
        margin[i] = top - second

    stats = {
        "n_shared_genes": n_shared,
        "n_hvg": int(q.n_vars),
        "n_ref": int(r.n_obs),
        "n_query": int(query.n_obs),
        "k": kk,
        "label_col": label_col,
        "backend": "knn",
    }
    return labels, frac, margin, stats


def ingest_label_transfer(
    query,
    reference,
    *,
    label_col: str,
    n_pcs: int = 30,
    max_ref_cells: int = 20000,
    seed: int = 66,
) -> tuple[list[str], np.ndarray, np.ndarray, dict]:
    """scanpy.tl.ingest (same genes required). Confidence is 1.0 (no vote)."""
    genes = query.var_names.intersection(reference.var_names)
    if len(genes) < 50:
        raise ValueError(f"Too few shared genes ({len(genes)}) for ingest.")
    genes = genes[: min(len(genes), 4000)]
    r = _subsample_ref(reference[:, genes].copy(), label_col, max_ref_cells, seed=seed)
    q = query[:, genes].copy()
    _lognorm(r)
    _lognorm(q)
    n_comps = min(n_pcs, r.n_obs - 1, r.n_vars - 1)
    sc.pp.pca(r, n_comps=max(2, n_comps), zero_center=False)
    sc.pp.neighbors(r, n_neighbors=min(15, r.n_obs - 1))
    sc.tl.umap(r, min_dist=0.3)
    sc.tl.ingest(q, r, obs=label_col)
    labels = q.obs[label_col].astype(str).tolist()
    if "X_umap" in q.obsm:
        query.obsm["X_umap"] = q.obsm["X_umap"]
    if "X_pca" in q.obsm:
        query.obsm["X_pca"] = q.obsm["X_pca"]
    n = len(labels)
    frac = np.ones(n, dtype=np.float64)
    margin = np.zeros(n, dtype=np.float64)
    stats = {
        "n_shared_genes": int(len(genes)),
        "n_ref": int(r.n_obs),
        "n_query": int(query.n_obs),
        "label_col": label_col,
        "backend": "ingest",
    }
    return labels, frac, margin, stats


def transfer_labels(
    query,
    reference,
    *,
    label_col: str | None = None,
    backend: str = "knn",
    k: int = 15,
    n_pcs: int = 30,
    n_hvg: int = 2000,
    max_ref_cells: int = 20000,
    seed: int = 66,
) -> dict:
    col = resolve_reference_label(reference, label_col)
    backend = (backend or "knn").lower()
    if backend == "ingest":
        try:
            labels, frac, margin, stats = ingest_label_transfer(
                query,
                reference,
                label_col=col,
                n_pcs=n_pcs,
                max_ref_cells=max_ref_cells,
                seed=seed,
            )
        except Exception as e:
            print(f"  ingest failed ({e}); falling back to knn")
            backend = "knn"
    if backend != "ingest":
        if backend not in {"knn", "auto"}:
            print(f"  Unknown backend {backend!r}; using knn")
        labels, frac, margin, stats = knn_label_transfer(
            query,
            reference,
            label_col=col,
            k=k,
            n_pcs=n_pcs,
            n_hvg=n_hvg,
            max_ref_cells=max_ref_cells,
            seed=seed,
        )
    return {
        "labels": labels,
        "score": frac,
        "margin": margin,
        "stats": stats,
        "label_col": col,
    }
