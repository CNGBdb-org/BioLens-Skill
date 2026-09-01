#!/usr/bin/env python3
"""
CIMA scRNA-seq 预处理 CPU 适配版
基于 CIMA/scRNA-seq/CIMA_scRNA_Preprocessing.py (作者: Yuhui Zheng)
适配: 无GPU环境, 4-16GB内存

用法:
  python3 scripts/cima_scrna_preprocessing_cpu.py \
    --input /path/to/data.h5ad \
    --output /path/to/output/ \
    --profile auto
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import time

import numpy as np
import pandas as pd
import scanpy as sc


def parse_args():
    p = argparse.ArgumentParser(description="CIMA scRNA-seq Preprocessing (CPU)")
    p.add_argument("--input", required=True, help="Input h5ad file path")
    p.add_argument("--output", required=True, help="Output directory")
    p.add_argument(
        "--profile",
        choices=["auto", "large", "small"],
        default="auto",
        help="auto: <100 samples or <15k cells → small; large=CIMA-scale defaults",
    )
    p.add_argument("--n-target", type=int, default=None, help="Subsample target (large default 50000)")
    p.add_argument("--hvg-n", type=int, default=None, help="HVG count (large 2500 / small 1500)")
    p.add_argument("--resolution", type=float, default=None, help="Leiden resolution (large 1.5 / small 1.0)")
    p.add_argument("--n-pcs", type=int, default=None, help="PCs for neighbors (large 19 / small 12)")
    p.add_argument("--n-neighbors", type=int, default=None, help="kNN size (large 30 / small 15)")
    p.add_argument("--batch-key", default="sample", help="Batch key for Harmony (empty=skip)")
    p.add_argument("--celltype-col", default="cell_type", help="Existing cell type column")
    p.add_argument("--sample-col", default="sample_id", help="Sample ID column")
    p.add_argument("--skip-harmony", action="store_true", help="Skip Harmony")
    p.add_argument("--skip-subsampling", action="store_true", help="Skip subsampling")
    p.add_argument(
        "--small-sample-max",
        type=int,
        default=100,
        help="auto profile: n_samples below this → small",
    )
    p.add_argument(
        "--small-cell-max",
        type=int,
        default=15000,
        help="auto profile: n_obs below this → small",
    )
    return p.parse_args()


CELLTYPE_MAP = {
    "CD14 monocyte": "cMono",
    "CD16 monocyte": "ncMono",
    "CD14/CD16 monocyte": "cMono",
    "Memory CD4 T cell": "T cells",
    "Naive CD4 T cell": "T cells",
    "GZMB CD8 T cell": "T cells",
    "GZMK CD8 T cell": "T cells",
    "Naive CD8 T cell": "T cells",
    "Cycling T/NK cell": "T cells",
    "MAIT cell": "T cells",
    "Treg cell": "T cells",
    "Gamma delta T cell": "T cells",
    "CD16 NK cell": "NK cells",
    "CD56 NK cell": "NK cells",
    "Naive B cell": "Naive B",
    "Memory B cell": "Memory B",
    "Plasma cell": "Plasma&Cycling T",
    "Megakaryocyte": "Megakaryocyte",
    "pDC": "pDC",
    "Dendritic cell": "cDC",
    "Cycling myeloid cell": "cDC",
    "Hematopoietic stem cell": "HSPC",
    "Neutrophil": "ncMono",
    "Red blood cell": "Erythrocyte",
}

LINEAGES = {
    "B_cells": ["Naive B", "Memory B", "Plasma&Cycling T"],
    "myeloid": ["pDC", "cDC", "cMono", "ncMono", "Megakaryocyte", "HSPC"],
    "TNK": ["T cells", "NK cells"],
    "erythrocyte": ["Erythrocyte"],
}


def _n_samples(adata, sample_key: str = "sample") -> int:
    if sample_key in adata.obs.columns:
        return int(adata.obs[sample_key].astype(str).nunique())
    return 1


def resolve_profile(args, *, n_obs: int, n_samples: int) -> tuple[str, list[str]]:
    """Pick large/small and fill unset numeric flags. Returns (profile, reasons)."""
    reasons: list[str] = []
    profile = args.profile
    if profile == "auto":
        if n_samples < args.small_sample_max:
            profile = "small"
            reasons.append(f"n_samples={n_samples} < {args.small_sample_max}")
        elif n_obs < args.small_cell_max:
            profile = "small"
            reasons.append(f"n_obs={n_obs} < {args.small_cell_max}")
        else:
            profile = "large"
            reasons.append(f"n_samples={n_samples}, n_obs={n_obs} → large")

    if profile == "small":
        if args.n_target is None:
            args.n_target = max(n_obs, 1)
        if args.hvg_n is None:
            args.hvg_n = 1500
        if args.resolution is None:
            args.resolution = 1.0
        if args.n_pcs is None:
            args.n_pcs = 12
        if args.n_neighbors is None:
            args.n_neighbors = 15
        args.skip_subsampling = True
        # Few batches: Harmony often hurts more than helps
        if n_samples < 50:
            args.skip_harmony = True
            reasons.append(f"n_samples={n_samples} < 50 → skip Harmony")
    else:
        if args.n_target is None:
            args.n_target = 50000
        if args.hvg_n is None:
            args.hvg_n = 2500
        if args.resolution is None:
            args.resolution = 1.5
        if args.n_pcs is None:
            args.n_pcs = 19
        if args.n_neighbors is None:
            args.n_neighbors = 30

    return profile, reasons


def main():
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(os.path.join(args.output, "figures"), exist_ok=True)
    sc.settings.figdir = os.path.join(args.output, "figures")
    sc.settings.verbosity = 2
    np.random.seed(66)
    t0 = time.time()

    print(f"[1] Reading {args.input} ...")
    adata = sc.read_h5ad(args.input)
    print(f"    Shape: {adata.shape}")

    if args.sample_col in adata.obs.columns:
        adata.obs["sample"] = adata.obs[args.sample_col].astype(str)
    elif "sample" not in adata.obs.columns:
        adata.obs["sample"] = "unknown"

    n_samples = _n_samples(adata, "sample")
    profile, reasons = resolve_profile(args, n_obs=adata.n_obs, n_samples=n_samples)
    print(f"    Profile: {profile} ({'; '.join(reasons) if reasons else 'explicit'})")
    print(
        f"    Params: hvg_n={args.hvg_n}, resolution={args.resolution}, "
        f"n_pcs={args.n_pcs}, n_neighbors={args.n_neighbors}, "
        f"skip_subsample={args.skip_subsampling}, skip_harmony={args.skip_harmony}"
    )
    with open(os.path.join(args.output, "preprocessing_profile.json"), "w", encoding="utf-8") as f:
        json.dump(
            {
                "profile": profile,
                "reasons": reasons,
                "n_obs": int(adata.n_obs),
                "n_samples": n_samples,
                "hvg_n": args.hvg_n,
                "resolution": args.resolution,
                "n_pcs": args.n_pcs,
                "n_neighbors": args.n_neighbors,
                "skip_subsampling": args.skip_subsampling,
                "skip_harmony": args.skip_harmony,
            },
            f,
            indent=2,
        )

    if args.celltype_col in adata.obs.columns:
        adata.obs["celltype_1st"] = adata.obs[args.celltype_col].map(CELLTYPE_MAP).fillna("doublet")
        adata.obs["final_annotation"] = adata.obs[args.celltype_col].astype(str)

    for col, default in [("age", "NA"), ("sex", "NA")]:
        if col in adata.obs.columns:
            adata.obs[col] = adata.obs[col].astype(str).replace("nan", default)
        elif "gender" in adata.obs.columns and col == "sex":
            adata.obs["sex"] = adata.obs["gender"].astype(str).replace("nan", default)

    if not args.skip_subsampling and adata.n_obs > args.n_target:
        print(f"[2] Stratified subsampling to {args.n_target} ...")
        if "celltype_1st" in adata.obs.columns:
            vc = adata.obs["celltype_1st"].value_counts()
            selected_idx = []
            for ct, n in vc.items():
                n_sample = max(int(n * args.n_target / adata.n_obs), 100)
                n_sample = min(n_sample, n)
                idx = adata.obs.index[adata.obs["celltype_1st"] == ct].to_numpy()
                chosen = np.random.choice(idx, size=n_sample, replace=False)
                selected_idx.extend(chosen)
            adata = adata[selected_idx].copy()
        else:
            n_sub = min(args.n_target, adata.n_obs)
            selected = np.random.choice(adata.obs_names, size=n_sub, replace=False)
            adata = adata[selected].copy()
        gc.collect()
    else:
        print("[2] Skipping subsampling ...")
    print(f"    After subsampling: {adata.shape}")

    print("[3] QC ...")
    adata.var["mt"] = adata.var_names.str.startswith("MT-")
    adata.var["hb"] = adata.var_names.str.contains(r"^HB[^(P)]")
    adata.var["rp"] = adata.var_names.str.match(r"^RP[SL][0-9]")
    sc.pp.calculate_qc_metrics(adata, qc_vars=["mt", "rp"], percent_top=None, log1p=False, inplace=True)
    if "pct_counts_mt" in adata.obs.columns:
        adata = adata[adata.obs["pct_counts_mt"] < 20, :]
    sc.pp.filter_genes(adata, min_cells=3)
    sc.pp.filter_cells(adata, min_genes=200)
    print(f"    After QC: {adata.shape}")

    print("[4] Normalize + HVG ...")
    if "counts" not in adata.layers:
        adata.layers["counts"] = adata.X.copy()
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    sc.pp.highly_variable_genes(
        adata,
        n_top_genes=args.hvg_n,
        flavor="seurat",
        batch_key="sample" if "sample" in adata.obs.columns else None,
    )
    rm = (
        adata.var_names.str.match(r"^MT-")
        | adata.var_names.str.match(r"^RP[SL]")
        | adata.var_names.str.match(r"^[A-Z][A-Z][0-9].*\.[0-9]")
        | adata.var_names.str.match(r"(^LOC|LINC)[1-9]*")
    )
    adata.var.loc[rm, "highly_variable"] = False
    n_hvg = int(adata.var["highly_variable"].sum())
    print(f"    HVG: {n_hvg}")
    hvg_keep = adata.var_names[adata.var["highly_variable"]].tolist()
    pd.DataFrame(hvg_keep, columns=["hvg"]).to_csv(
        os.path.join(args.output, "CIMA_hvg_keep.csv"), index=False
    )

    print("[5] Subset to HVG only ...")
    adata = adata[:, adata.var["highly_variable"]].copy()
    gc.collect()
    print(f"    {adata.shape}")

    n_comps = min(50 if profile == "large" else 30, adata.n_obs - 1, adata.n_vars - 1)
    print(f"[6] PCA (n_comps={n_comps}, skip scale for numpy compat) ...")
    sc.tl.pca(adata, n_comps=max(2, n_comps), zero_center=False)

    if not args.skip_harmony and args.batch_key and args.batch_key in adata.obs.columns:
        print(f"[7] Harmony (key={args.batch_key}) ...")
        try:
            sc.external.pp.harmony_integrate(adata, args.batch_key)
            use_rep = "X_pca_harmony"
        except Exception as e:
            print(f"    Harmony failed: {e}. Using X_pca.")
            use_rep = "X_pca"
    else:
        print("[7] Skipping Harmony ...")
        use_rep = "X_pca"

    leiden_key = f"leiden_r{args.resolution}"
    print("[8] Neighbors + UMAP + Leiden ...")
    n_pcs = min(args.n_pcs, adata.obsm["X_pca"].shape[1] - 1)
    sc.pp.neighbors(
        adata,
        n_neighbors=min(args.n_neighbors, max(2, adata.n_obs - 1)),
        n_pcs=max(1, n_pcs),
        use_rep=use_rep,
    )
    sc.tl.umap(adata, min_dist=0.3)
    sc.tl.leiden(
        adata,
        resolution=args.resolution,
        n_iterations=2,
        key_added=leiden_key,
        flavor="igraph",
        directed=False,
    )
    # Keep legacy alias used by some downstream demos
    adata.obs["leiden_r1.5_n2"] = adata.obs[leiden_key].astype(str)
    print(f"    Clusters ({leiden_key}): {adata.obs[leiden_key].nunique()}")

    print("[9] Annotation ...")
    sc.settings.set_figure_params(dpi=120, dpi_save=300)
    plot_kw = dict(legend_loc="right margin", frameon=False, show=False)
    if "celltype_1st" in adata.obs.columns:
        for ext in ("png", "pdf"):
            sc.pl.umap(adata, color="celltype_1st", save=f"_celltype_1st.{ext}", **plot_kw)
    else:
        adata.obs["celltype_1st"] = adata.obs[leiden_key].astype(str)
        print("    Warning: No cell type column. Using Leiden IDs. Annotate manually.")
    for ext in ("png", "pdf"):
        sc.pl.umap(adata, color=leiden_key, save=f"_leiden.{ext}", **plot_kw)

    print("[10] Save + Lineage split ...")
    out_file = os.path.join(args.output, "CIMA_Annotation_1st.h5ad")
    adata.write_h5ad(out_file)
    print(f"    Saved: {out_file} ({os.path.getsize(out_file) / 1e6:.0f}MB)")

    if "celltype_1st" in adata.obs.columns:
        for name, types in LINEAGES.items():
            mask = adata.obs["celltype_1st"].isin(types)
            if mask.sum() > 0:
                sub = adata[mask].copy()
                sub_file = os.path.join(args.output, f"CIMA_{name}.h5ad")
                sub.write_h5ad(sub_file)
                print(f"    {name}: {sub.n_obs} cells -> {sub_file}")
                del sub
                gc.collect()

    del adata
    gc.collect()
    print(f"\nDone ({(time.time() - t0) / 60:.1f}min) profile={profile}")


if __name__ == "__main__":
    main()
