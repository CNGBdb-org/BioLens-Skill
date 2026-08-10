#!/usr/bin/env python3
"""Peak matrix → gene activity helpers for CIMA scATAC / multi-omics.

Supports:
  1) adata.var['linked_gene'] (or --gene-col): sum peaks per gene
  2) gene_names list: round-robin / index map peak_i → gene_names[i % n] (demo)
  3) Pass-through when matrix already uses gene symbols
"""
from __future__ import annotations

import re
from typing import Iterable, Optional, Sequence

import anndata as ad
import numpy as np
import pandas as pd
from scipy import sparse

_PEAK_RE = re.compile(
    r"^(?:chr)?[\w.\-]+[:_](\d+)[-_](\d+)$",
    re.IGNORECASE,
)


def is_peak_like_name(name: str) -> bool:
    s = str(name)
    if ":" in s and "-" in s.split(":")[-1]:
        return True
    return bool(_PEAK_RE.match(s))


def is_peak_matrix(adata, sample: int = 80, frac: float = 0.5) -> bool:
    names = list(adata.var_names[: min(sample, adata.n_vars)])
    if not names:
        return False
    hits = sum(1 for n in names if is_peak_like_name(n))
    return (hits / len(names)) >= frac


def _as_csr(X):
    if sparse.issparse(X):
        return X.tocsr()
    return sparse.csr_matrix(np.asarray(X))


def peaks_to_gene_activity(
    adata: ad.AnnData,
    *,
    gene_col: str = "linked_gene",
    gene_names: Optional[Sequence[str]] = None,
    layer: Optional[str] = None,
) -> ad.AnnData:
    """Aggregate peak accessibility into a gene × cell activity matrix.

    Priority for peak→gene links:
      1. ``adata.var[gene_col]`` if present
      2. ``gene_names``: peak i maps to ``gene_names[i % len(gene_names)]``
    """
    if gene_col in adata.var.columns:
        links = adata.var[gene_col].astype(str).tolist()
    elif gene_names is not None and len(gene_names) > 0:
        genes = [str(g) for g in gene_names]
        links = [genes[i % len(genes)] for i in range(adata.n_vars)]
    else:
        raise ValueError(
            "Peak matrix needs gene links: provide var['{col}'] or gene_names "
            "(e.g. RNA var_names / --gene-list).".format(col=gene_col)
        )

    X = adata.layers[layer] if layer and layer in adata.layers else adata.X
    X = _as_csr(X)

    link_s = pd.Series(links, index=adata.var_names)
    # Drop empty / nan links
    link_s = link_s.replace({"": np.nan, "nan": np.nan, "None": np.nan}).dropna()
    if link_s.empty:
        raise ValueError("No valid peak→gene links after filtering")

    # Sum columns that share the same gene
    gene_order = list(dict.fromkeys(link_s.tolist()))  # stable unique
    gene_to_idx = {g: i for i, g in enumerate(gene_order)}
    # Build peak→gene sparse aggregator (n_peaks × n_genes) then X @ A
    rows, cols, data = [], [], []
    var_index = {v: i for i, v in enumerate(adata.var_names)}
    for peak, gene in link_s.items():
        pi = var_index[peak]
        rows.append(pi)
        cols.append(gene_to_idx[gene])
        data.append(1.0)
    A = sparse.csr_matrix(
        (data, (rows, cols)), shape=(adata.n_vars, len(gene_order))
    )
    Xg = X @ A

    out = ad.AnnData(
        X=Xg,
        obs=adata.obs.copy(),
        var=pd.DataFrame(index=pd.Index(gene_order, name="gene")),
    )
    # Carry useful embeddings / clusters from peak object
    for key in ("X_pca", "X_pca_harmony", "X_umap"):
        if key in adata.obsm:
            out.obsm[key] = adata.obsm[key].copy()
    for col in ("leiden", "sample", "celltype_1st", "batch"):
        if col in adata.obs.columns and col not in out.obs.columns:
            out.obs[col] = adata.obs[col].values
    out.uns["peak_to_gene"] = {
        "n_peaks": int(adata.n_vars),
        "n_genes": int(out.n_vars),
        "gene_col": gene_col if gene_col in adata.var.columns else None,
        "mode": "linked_gene" if gene_col in adata.var.columns else "gene_names_map",
    }
    return out


def ensure_gene_level_atac(
    atac: ad.AnnData,
    *,
    rna_genes: Optional[Iterable[str]] = None,
    gene_col: str = "linked_gene",
) -> tuple[ad.AnnData, bool]:
    """Return (gene-level adata, converted_from_peaks)."""
    if not is_peak_matrix(atac):
        return atac, False
    genes = list(rna_genes) if rna_genes is not None else None
    converted = peaks_to_gene_activity(atac, gene_col=gene_col, gene_names=genes)
    return converted, True
