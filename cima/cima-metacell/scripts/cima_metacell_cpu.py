#!/usr/bin/env python3
"""CIMA Metacell generation (CPU fallback, no SEACells).

Per sample×celltype: KMeans (or single metacell if few cells) → sum aggregation.
Optional ATAC h5ad; if omitted, builds a mock peak matrix from RNA for pairing smoke tests.

Usage:
  python3 cima_metacell_cpu.py \\
    --rna /path/to/rna.h5ad \\
    --atac /path/to/atac.h5ad \\
    --output ./step6_output/
"""
from __future__ import annotations

import argparse
import gc
import os
import time

import numpy as np
import pandas as pd
import scanpy as sc
from scipy.sparse import csr_matrix, issparse
from sklearn.cluster import KMeans


def parse_args():
    p = argparse.ArgumentParser(description="CIMA Metacell Generation (CPU)")
    p.add_argument("--rna", required=True, help="scRNA h5ad (with sample + celltype)")
    p.add_argument("--atac", default=None, help="Optional scATAC h5ad")
    p.add_argument("--output", required=True, help="Output directory")
    p.add_argument("--sample-col", default="sample")
    p.add_argument("--celltype-col", default="celltype_1st",
                   help="Cell type column (will also write cell_type_l4)")
    p.add_argument("--cells-per-mc", type=int, default=50)
    return p.parse_args()


def assign_metacell_labels_kmeans(ad, sample_col="sample", ct_col="cell_type_l4", cells_per_mc=50):
    ad.obs["SEACell_ID"] = "unassigned"
    for sample in ad.obs[sample_col].astype(str).unique():
        smask = ad.obs[sample_col].astype(str) == sample
        for ct in ad.obs.loc[smask, ct_col].astype(str).unique():
            cmask = smask & (ad.obs[ct_col].astype(str) == ct)
            n_cells = int(cmask.sum())
            if n_cells == 0:
                continue
            if n_cells < 100:
                ad.obs.loc[cmask, "SEACell_ID"] = f"{sample}-{ct}-SEACell-0"
                continue
            n_mc = max(int(n_cells / cells_per_mc), 2)
            sub = ad[cmask].copy()
            if "counts" in sub.layers:
                sub.X = sub.layers["counts"].copy()
            sc.pp.normalize_total(sub, target_sum=1e4)
            sc.pp.log1p(sub)
            n_comps = min(15, sub.n_obs - 1, sub.n_vars - 1)
            if n_comps < 2:
                ad.obs.loc[cmask, "SEACell_ID"] = f"{sample}-{ct}-SEACell-0"
                continue
            sc.tl.pca(sub, n_comps=n_comps, zero_center=False)
            labels = KMeans(n_clusters=n_mc, random_state=66, n_init=10).fit_predict(sub.obsm["X_pca"])
            ad.obs.loc[cmask, "SEACell_ID"] = [f"{sample}-{ct}-SEACell-{l}" for l in labels]
    print(f"  Metacells assigned: {ad.obs['SEACell_ID'].nunique()}")


def summarize_by_metacell(ad, mc_col="SEACell_ID"):
    mcs = ad.obs[mc_col].unique()
    rows = []
    for m in mcs:
        cells = ad.obs_names[ad.obs[mc_col] == m]
        x = ad[cells, :].X
        if issparse(x):
            s = np.ravel(x.sum(axis=0))
        else:
            s = np.ravel(np.asarray(x).sum(axis=0))
        rows.append(s)
    summ = np.vstack(rows).astype(np.float32)
    meta_ad = sc.AnnData(csr_matrix(summ))
    meta_ad.obs_names = pd.Index(mcs.astype(str))
    meta_ad.var_names = ad.var_names
    for col in ["sample", "cell_type_l4", "celltype_1st", "age", "sex"]:
        if col in ad.obs.columns:
            grouped = ad.obs.groupby(mc_col, observed=False)[col].first()
            meta_ad.obs[col] = grouped.reindex(mcs).values
    return meta_ad


def ensure_celltype(ad, celltype_col):
    if celltype_col in ad.obs.columns:
        ad.obs["cell_type_l4"] = ad.obs[celltype_col].astype(str)
    elif "cell_type_l4" not in ad.obs.columns:
        raise SystemExit(f"Missing cell type column '{celltype_col}' (and no cell_type_l4)")
    if "sample" not in ad.obs.columns:
        raise SystemExit("Missing 'sample' column in .obs")


def mock_atac_from_rna(rna, n_peaks=100):
    rng = np.random.default_rng(42)
    peak_names = [f"peak_{i}" for i in range(n_peaks)]
    x = rng.lognormal(mean=1.0, sigma=0.5, size=(rna.n_obs, n_peaks)).astype(np.float32)
    atac = sc.AnnData(X=x, obs=rna.obs.copy())
    atac.var_names = peak_names
    return atac


def pair_pseudo_multiomics(rna_mc, atac_mc, out_dir):
    common_cts = set(rna_mc.obs["cell_type_l4"].astype(str)) & set(atac_mc.obs["cell_type_l4"].astype(str))
    rna_mc = rna_mc[rna_mc.obs["cell_type_l4"].astype(str).isin(common_cts)].copy()
    atac_mc = atac_mc[atac_mc.obs["cell_type_l4"].astype(str).isin(common_cts)].copy()
    print(f"\nCommon cell types: {len(common_cts)}")

    rna_mc.obs["new_barcode"] = ""
    atac_mc.obs["new_barcode"] = ""
    new_barcodes = []
    for (sample, ct), rna_grp in rna_mc.obs.groupby(["sample", "cell_type_l4"], observed=False):
        atac_grp = atac_mc.obs[
            (atac_mc.obs["sample"].astype(str) == str(sample))
            & (atac_mc.obs["cell_type_l4"].astype(str) == str(ct))
        ]
        if rna_grp.empty or atac_grp.empty:
            continue
        min_n = min(len(rna_grp), len(atac_grp))
        rna_idx = rna_grp.sample(n=min_n, random_state=42).index
        atac_idx = atac_grp.sample(n=min_n, random_state=42).index
        for i in range(min_n):
            bc = f"{sample}_{ct}_{i + 1}"
            rna_mc.obs.at[rna_idx[i], "new_barcode"] = bc
            atac_mc.obs.at[atac_idx[i], "new_barcode"] = bc
            new_barcodes.append({"new_barcode": bc, "sample": sample, "cell_type": ct})

    barcode_df = pd.DataFrame(new_barcodes)
    barcode_df.to_csv(os.path.join(out_dir, "Pseudo_multiomics_barcode_info.csv"), index=False)
    print(f"Paired barcodes: {len(barcode_df)}")

    rna_filt = rna_mc[rna_mc.obs["new_barcode"] != ""].copy()
    atac_filt = atac_mc[atac_mc.obs["new_barcode"] != ""].copy()
    rna_filt.write_h5ad(os.path.join(out_dir, "CIMA_scRNA_Pseudo_multiomics.h5ad"))
    atac_filt.write_h5ad(os.path.join(out_dir, "CIMA_scATAC_Pseudo_multiomics.h5ad"))
    print(f"Pseudo-multiomics RNA: {rna_filt.shape}")
    print(f"Pseudo-multiomics ATAC: {atac_filt.shape}")


def main():
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)
    np.random.seed(66)
    t0 = time.time()

    print(f"Loading RNA: {args.rna}")
    rna = sc.read_h5ad(args.rna)
    ensure_celltype(rna, args.celltype_col)
    print(f"  RNA: {rna.shape}, cell types: {rna.obs['cell_type_l4'].nunique()}")

    print("\n[1] Assign RNA metacells...")
    assign_metacell_labels_kmeans(
        rna, sample_col=args.sample_col, ct_col="cell_type_l4", cells_per_mc=args.cells_per_mc
    )
    rna.obs[["SEACell_ID"]].to_csv(os.path.join(args.output, "CIMA_scRNA_Metacell.csv"))
    rna_mc = summarize_by_metacell(rna)
    rna_mc_path = os.path.join(args.output, "CIMA_scRNA_Metacell.h5ad")
    rna_mc.write_h5ad(rna_mc_path)
    print(f"  Saved {rna_mc_path} {rna_mc.shape}")

    print("\n[2] ATAC metacells...")
    if args.atac:
        atac = sc.read_h5ad(args.atac)
        ensure_celltype(atac, args.celltype_col if args.celltype_col in atac.obs.columns else "cell_type_l4")
        if args.celltype_col in atac.obs.columns and "cell_type_l4" not in atac.obs.columns:
            atac.obs["cell_type_l4"] = atac.obs[args.celltype_col].astype(str)
        if "sample" not in atac.obs.columns:
            raise SystemExit("ATAC missing 'sample' column")
        print(f"  ATAC input: {atac.shape}")
    else:
        print("  No --atac given; building mock peak ATAC from RNA for pairing smoke test")
        atac = mock_atac_from_rna(rna)

    assign_metacell_labels_kmeans(
        atac, sample_col=args.sample_col, ct_col="cell_type_l4", cells_per_mc=args.cells_per_mc
    )
    atac.obs[["SEACell_ID"]].to_csv(os.path.join(args.output, "CIMA_scATAC_Metacell.csv"))
    atac_mc = summarize_by_metacell(atac)
    atac_mc_path = os.path.join(args.output, "CIMA_scATAC_Metacell.h5ad")
    atac_mc.write_h5ad(atac_mc_path)
    print(f"  Saved {atac_mc_path} {atac_mc.shape}")

    print("\n[3] Pseudo-multiomics pairing...")
    pair_pseudo_multiomics(rna_mc, atac_mc, args.output)

    gc.collect()
    print(f"\nDone ({(time.time() - t0) / 60:.1f} min). Output: {args.output}")


if __name__ == "__main__":
    main()
