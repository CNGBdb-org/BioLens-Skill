#!/usr/bin/env python3
"""CIMA scATAC-seq Preprocessing (CPU fallback)

Replaces SnapATAC2 spectral embedding with TF-IDF + TruncatedSVD.
No GPU required.

Also writes gene-activity matrix (peak→gene) for Step 5 multi-omics when
``var['linked_gene']`` is present or ``--gene-list`` / ``--rna`` is given.

Usage:
  python3 cima_scratac_cpu.py --input peak_matrix.h5ad --output ./step4_output/
"""
import argparse
import os
import sys

import numpy as np
import scanpy as sc
from scipy.sparse import issparse
from sklearn.decomposition import TruncatedSVD

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from cima_peak_to_gene import is_peak_matrix, peaks_to_gene_activity  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="CIMA scATAC-seq Preprocessing (CPU)")
    p.add_argument("--input", required=True, help="Peak-by-cell h5ad file")
    p.add_argument("--output", required=True, help="Output directory")
    p.add_argument("--n-components", type=int, default=50, help="SVD components (default 50)")
    p.add_argument("--batch-key", default=None, help="Batch key for Harmony")
    p.add_argument("--resolution", type=float, default=1.0, help="Leiden resolution")
    p.add_argument("--skip-harmony", action="store_true")
    p.add_argument(
        "--skip-gene-activity",
        action="store_true",
        help="Do not write gene-activity h5ad",
    )
    p.add_argument(
        "--gene-col",
        default="linked_gene",
        help="Peak→gene column in var (default: linked_gene)",
    )
    p.add_argument(
        "--gene-list",
        default=None,
        help="Optional text file of gene symbols (one per line) for peak→gene map",
    )
    p.add_argument(
        "--rna",
        default=None,
        help="Optional RNA h5ad; use its var_names to map peaks→genes when no linked_gene",
    )
    p.add_argument(
        "--min-peaks-per-cell",
        type=int,
        default=50,
        help="min peaks/genes per cell filter (default 50; lower for tiny demos)",
    )
    return p.parse_args()


def _load_gene_names(args):
    if args.gene_list:
        with open(args.gene_list) as f:
            return [ln.strip() for ln in f if ln.strip()]
    if args.rna:
        rna = sc.read_h5ad(args.rna, backed="r")
        return list(rna.var_names)
    return None


def main():
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(os.path.join(args.output, "figures"), exist_ok=True)
    sc.settings.figdir = os.path.join(args.output, "figures")
    sc.settings.verbosity = 2
    np.random.seed(42)

    print(f"Loading {args.input}...")
    adata = sc.read_h5ad(args.input)
    print(f"  Shape: {adata.shape}  peak_matrix={is_peak_matrix(adata)}")

    # Keep a raw peak copy for gene activity (before TF-IDF)
    adata_raw = adata.copy()

    # QC
    print("\n[1/6] QC filtering...")
    sc.pp.filter_cells(adata, min_genes=min(args.min_peaks_per_cell, max(1, adata.n_vars // 4)))
    sc.pp.filter_genes(adata, min_cells=1)
    adata_raw = adata_raw[adata.obs_names, adata.var_names].copy()

    # TF-IDF normalization
    print("[2/6] TF-IDF normalization...")
    if issparse(adata.X):
        adata.X = adata.X.tocsc()

    sc.pp.normalize_total(adata, target_sum=1e4)
    n_cells = adata.n_obs
    peak_counts = np.array((adata.X > 0).sum(axis=0)).flatten()
    idf = np.log1p(n_cells / (peak_counts + 1))
    adata.X = adata.X.multiply(idf).tocsr()
    del peak_counts, idf

    print(f"[3/6] TruncatedSVD ({args.n_components} PCs)...")
    n_comp = min(args.n_components, adata.n_obs - 1, adata.n_vars - 1)
    svd = TruncatedSVD(n_components=max(2, n_comp), random_state=42)
    adata.obsm["X_pca"] = svd.fit_transform(adata.X)
    print(f"  Explained variance: {svd.explained_variance_ratio_.sum():.2%}")

    use_rep = "X_pca"
    if not args.skip_harmony and args.batch_key and args.batch_key in adata.obs.columns:
        try:
            print("[4/6] Harmony batch correction...")
            sc.external.pp.harmony_integrate(adata, args.batch_key)
            use_rep = "X_pca_harmony"
        except Exception as e:
            print(f"  Harmony skipped: {e}")
    else:
        print("[4/6] Harmony skipped")

    print("[5/6] Neighbors, UMAP, Leiden...")
    sc.pp.neighbors(
        adata,
        n_neighbors=min(15, adata.n_obs - 1),
        n_pcs=min(30, adata.obsm["X_pca"].shape[1]),
        use_rep=use_rep,
    )
    sc.tl.umap(adata, min_dist=0.3)
    sc.tl.leiden(adata, resolution=args.resolution, key_added="leiden", flavor="igraph")

    peak_out = os.path.join(args.output, "CIMA_scATAC_peaks.h5ad")
    adata.write_h5ad(peak_out)
    # Backward-compatible alias (historical name; still peak space)
    alias = os.path.join(args.output, "pbmc_filtered_genescore.h5ad")
    adata.write_h5ad(alias)
    print(f"\nSaved peaks: {peak_out} ({os.path.getsize(peak_out)/1e6:.1f}MB)")
    print(f"  Clusters: {adata.obs['leiden'].nunique()}")

    # Gene activity for Step 5
    if not args.skip_gene_activity and is_peak_matrix(adata_raw):
        print("[6/6] Peak → gene activity...")
        gene_names = _load_gene_names(args)
        try:
            # Prefer counts before TF-IDF for activity
            gene_ad = peaks_to_gene_activity(
                adata_raw, gene_col=args.gene_col, gene_names=gene_names
            )
            # Attach peak-space clustering/UMAP
            gene_ad.obs["leiden"] = adata.obs.loc[gene_ad.obs_names, "leiden"].values
            if "X_umap" in adata.obsm:
                gene_ad.obsm["X_umap"] = adata[gene_ad.obs_names].obsm["X_umap"]
            gene_out = os.path.join(args.output, "CIMA_scATAC_gene_activity.h5ad")
            gene_ad.write_h5ad(gene_out)
            print(
                f"Saved gene activity: {gene_out} "
                f"({gene_ad.n_obs} × {gene_ad.n_vars}, {os.path.getsize(gene_out)/1e6:.1f}MB)"
            )
        except ValueError as e:
            print(f"  Gene activity skipped: {e}")
            print("  Tip: add var['linked_gene'], or pass --rna / --gene-list")
    else:
        print("[6/6] Gene activity skipped")

    sc.settings.set_figure_params(dpi=120, dpi_save=300)
    sc.pl.umap(adata, color="leiden", save="_atac_leiden.png", legend_loc="right margin", frameon=False, show=False)
    sc.pl.umap(adata, color="leiden", save="_atac_leiden.pdf", legend_loc="right margin", frameon=False, show=False)
    print("Done.")


if __name__ == "__main__":
    main()
