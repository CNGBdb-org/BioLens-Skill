#!/usr/bin/env python3
"""CIMA Multi-omics Integration (CPU fallback)

Replaces SCGLUE with gene-level PCA concatenation + KNN label transfer.
No GPU or pybedtools required.

ATAC input may be:
  - gene-level activity (preferred), or
  - peak matrix (auto-converted via var['linked_gene'] or RNA gene names)

Usage:
  python3 cima_multiomics_integration_cpu.py --rna rna.h5ad --atac atac.h5ad --output ./step5_output/
"""
import argparse
import os
import sys

import numpy as np
import pandas as pd
import scanpy as sc
from sklearn.neighbors import NearestNeighbors

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from cima_peak_to_gene import ensure_gene_level_atac, is_peak_matrix  # noqa: E402


def parse_args():
    p = argparse.ArgumentParser(description="CIMA Multi-omics Integration (CPU)")
    p.add_argument("--rna", required=True, help="scRNA h5ad file")
    p.add_argument(
        "--atac",
        required=True,
        help="scATAC h5ad: gene-level OR peak matrix (auto peak→gene)",
    )
    p.add_argument("--output", required=True, help="Output directory")
    p.add_argument("--n-hvg", type=int, default=2000, help="Number of HVGs (default 2000)")
    p.add_argument("--n-pcs", type=int, default=30, help="PCA components (default 30)")
    p.add_argument("--knn", type=int, default=30, help="KNN neighbors for label transfer (default 30)")
    p.add_argument("--batch-key", default=None, help="Batch key for Harmony")
    p.add_argument("--skip-harmony", action="store_true")
    p.add_argument(
        "--gene-col",
        default="linked_gene",
        help="If ATAC is peaks, column in var for peak→gene links",
    )
    return p.parse_args()


def main():
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(os.path.join(args.output, "figures"), exist_ok=True)
    sc.settings.figdir = os.path.join(args.output, "figures")
    sc.settings.verbosity = 2
    np.random.seed(42)

    # Load
    print(f"Loading RNA: {args.rna}")
    rna = sc.read_h5ad(args.rna)
    print(f"  RNA shape: {rna.shape}")

    print(f"Loading ATAC: {args.atac}")
    atac = sc.read_h5ad(args.atac)
    print(f"  ATAC shape: {atac.shape}  peak_matrix={is_peak_matrix(atac)}")

    # Auto peak → gene if needed
    atac, converted = ensure_gene_level_atac(
        atac, rna_genes=list(rna.var_names), gene_col=args.gene_col
    )
    if converted:
        print(f"  Converted peaks → gene activity: {atac.shape}")
        conv_path = os.path.join(args.output, "CIMA_scATAC_gene_activity_from_peaks.h5ad")
        atac.write_h5ad(conv_path)
        print(f"  Wrote: {conv_path}")

    # Find common genes
    common = sorted(set(rna.var_names) & set(atac.var_names))
    print(f"\n[1/6] Common genes: {len(common)}")
    if len(common) < 100:
        print("  WARNING: very few common genes. Ensure both use gene symbols.")

    rna = rna[:, common].copy()
    atac = atac[:, common].copy()

    # HVG on RNA
    print("[2/6] HVG selection...")
    sc.pp.normalize_total(rna, target_sum=1e4)
    sc.pp.log1p(rna)
    n_hvg = min(args.n_hvg, rna.n_vars)
    sc.pp.highly_variable_genes(rna, n_top_genes=n_hvg, flavor="seurat")
    hvg = rna.var_names[rna.var["highly_variable"]].tolist()
    print(f"  {len(hvg)} HVGs")

    rna = rna[:, hvg].copy()
    atac = atac[:, hvg].copy()
    sc.pp.normalize_total(atac, target_sum=1e4)
    sc.pp.log1p(atac)

    # PCA per modality
    print("[3/6] PCA per modality...")
    n_pcs = min(args.n_pcs, rna.n_obs - 1, rna.n_vars - 1, atac.n_obs - 1)
    n_pcs = max(2, n_pcs)
    sc.tl.pca(rna, n_comps=n_pcs, zero_center=False)
    sc.tl.pca(atac, n_comps=n_pcs, zero_center=False)

    # Concatenate into joint space
    rna_pca = rna.obsm["X_pca"]
    atac_pca = atac.obsm["X_pca"]
    joint = np.concatenate([rna_pca, atac_pca], axis=0)
    print(f"  Joint PCA shape: {joint.shape}")

    # Build combined AnnData
    combined = sc.concat([rna, atac], label="modality", keys=["RNA", "ATAC"])
    combined.obsm["X_pca"] = joint

    # Harmony (optional)
    use_rep = "X_pca"
    if not args.skip_harmony and args.batch_key and args.batch_key in combined.obs.columns:
        try:
            print("[4/6] Harmony batch correction...")
            sc.external.pp.harmony_integrate(combined, args.batch_key)
            use_rep = "X_pca_harmony"
        except Exception as e:
            print(f"  Harmony skipped: {e}")

    # UMAP on joint embedding
    print("[5/6] UMAP...")
    sc.pp.neighbors(
        combined,
        n_neighbors=min(15, combined.n_obs - 1),
        n_pcs=min(30, joint.shape[1]),
        use_rep=use_rep,
    )
    sc.tl.umap(combined, min_dist=0.3)

    # KNN label transfer: RNA → ATAC
    print(f"[6/6] KNN label transfer (k={args.knn})...")
    n_atac = atac.n_obs
    k = min(args.knn, rna.n_obs)

    # RNA cells have labels, ATAC cells don't
    if "celltype_1st" not in rna.obs.columns and "cell_type_l4" not in rna.obs.columns:
        print("  WARNING: no celltype column in RNA, using leiden as labels")
        if "leiden" not in rna.obs.columns:
            sc.tl.leiden(rna, resolution=1.0, key_added="leiden", flavor="igraph")
        label_col = "leiden"
    elif "cell_type_l4" in rna.obs.columns:
        label_col = "cell_type_l4"
    else:
        label_col = "celltype_1st"

    rna_labels = rna.obs[label_col].values

    # Fit KNN on RNA PCA, query ATAC PCA
    nn = NearestNeighbors(n_neighbors=k, metric="euclidean", n_jobs=-1)
    nn.fit(rna_pca)
    dist, idx = nn.kneighbors(atac_pca)

    # Majority vote
    transferred = []
    for i in range(n_atac):
        neighbor_labels = rna_labels[idx[i]]
        counts = pd.Series(neighbor_labels).value_counts()
        transferred.append(counts.index[0])

    # Add to ATAC and combined
    atac.obs["celltype_transferred"] = transferred

    # Build combined labels
    combined_labels = list(rna_labels) + transferred
    combined.obs["celltype"] = combined_labels

    print(f"  Transferred labels to {n_atac} ATAC cells")
    print(f"  Label distribution in ATAC: {pd.Series(transferred).value_counts().to_dict()}")

    # Ensure obs columns are h5ad-writable (mixed category/float age breaks h5py)
    def _sanitize_obs(ad):
        for c in list(ad.obs.columns):
            s = ad.obs[c]
            if getattr(s.dtype, "name", "") == "category" or s.dtype == object:
                ad.obs[c] = s.astype(str).replace({"nan": "NA", "None": "NA"})
            elif str(s.dtype).startswith(("float", "int")) and c in ("age", "sex", "sample"):
                ad.obs[c] = s.astype(str)
        return ad

    rna = _sanitize_obs(rna)
    atac = _sanitize_obs(atac)
    combined = _sanitize_obs(combined)
    atac = _sanitize_obs(atac)

    # Save
    combined_out = os.path.join(args.output, "CIMA_Combined.h5ad")
    combined.write_h5ad(combined_out)
    print(f"\nSaved combined: {combined_out} ({os.path.getsize(combined_out)/1e6:.1f}MB)")

    atac_out = os.path.join(args.output, "CIMA_scATAC_Annotation_Transfered.h5ad")
    atac.write_h5ad(atac_out)
    print(f"Saved ATAC labels: {atac_out} ({os.path.getsize(atac_out)/1e6:.1f}MB)")

    # Figures
    sc.settings.set_figure_params(dpi=120, dpi_save=300)
    for ext in ("png", "pdf"):
        sc.pl.umap(
            combined,
            color="modality",
            save=f"_multiomics_modality.{ext}",
            legend_loc="right margin",
            frameon=False,
            show=False,
        )
        sc.pl.umap(
            combined,
            color="celltype",
            save=f"_multiomics_celltype.{ext}",
            legend_loc="right margin",
            frameon=False,
            show=False,
        )
    print("Done.")


if __name__ == "__main__":
    main()
