#!/usr/bin/env python3
"""
CIMA scRNA-seq 预处理 CPU 适配版
基于 CIMA/scRNA-seq/CIMA_scRNA_Preprocessing.py (作者: Yuhui Zheng)
适配: 无GPU环境, 4-16GB内存

用法:
  python3 scripts/cima_scrna_preprocessing_cpu.py \
    --input /path/to/data.h5ad \
    --output /path/to/output/ \
    --n-target 50000 \
    --hvg-n 2500 \
    --celltype-col cell_type \
    --sample-col sample_id
"""
import argparse
import os
import gc
import time
import numpy as np
import pandas as pd
import scanpy as sc

def parse_args():
    p = argparse.ArgumentParser(description="CIMA scRNA-seq Preprocessing (CPU)")
    p.add_argument("--input", required=True, help="Input h5ad file path")
    p.add_argument("--output", required=True, help="Output directory")
    p.add_argument("--n-target", type=int, default=50000, help="Subsample target cell count")
    p.add_argument("--hvg-n", type=int, default=2500, help="Number of HVGs")
    p.add_argument("--resolution", type=float, default=1.5, help="Leiden resolution")
    p.add_argument("--batch-key", default="sample", help="Batch key for Harmony (empty=skip)")
    p.add_argument("--celltype-col", default="cell_type", help="Existing cell type column")
    p.add_argument("--sample-col", default="sample_id", help="Sample ID column")
    p.add_argument("--skip-harmony", action="store_true", help="Skip Harmony batch correction")
    p.add_argument("--skip-subsampling", action="store_true", help="Skip subsampling")
    return p.parse_args()

CELLTYPE_MAP = {
    'CD14 monocyte': 'cMono', 'CD16 monocyte': 'ncMono',
    'CD14/CD16 monocyte': 'cMono',
    'Memory CD4 T cell': 'T cells', 'Naive CD4 T cell': 'T cells',
    'GZMB CD8 T cell': 'T cells', 'GZMK CD8 T cell': 'T cells',
    'Naive CD8 T cell': 'T cells', 'Cycling T/NK cell': 'T cells',
    'MAIT cell': 'T cells', 'Treg cell': 'T cells',
    'Gamma delta T cell': 'T cells',
    'CD16 NK cell': 'NK cells', 'CD56 NK cell': 'NK cells',
    'Naive B cell': 'Naive B', 'Memory B cell': 'Memory B',
    'Plasma cell': 'Plasma&Cycling T',
    'Megakaryocyte': 'Megakaryocyte', 'pDC': 'pDC',
    'Dendritic cell': 'cDC', 'Cycling myeloid cell': 'cDC',
    'Hematopoietic stem cell': 'HSPC', 'Neutrophil': 'ncMono',
    'Red blood cell': 'Erythrocyte',
}

LINEAGES = {
    'B_cells': ['Naive B', 'Memory B', 'Plasma&Cycling T'],
    'myeloid': ['pDC', 'cDC', 'cMono', 'ncMono', 'Megakaryocyte', 'HSPC'],
    'TNK': ['T cells', 'NK cells'],
    'erythrocyte': ['Erythrocyte'],
}

def main():
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(os.path.join(args.output, 'figures'), exist_ok=True)
    sc.settings.figdir = os.path.join(args.output, 'figures')
    sc.settings.verbosity = 2
    np.random.seed(66)
    t0 = time.time()

    print(f"[1] Reading {args.input} ...")
    adata = sc.read_h5ad(args.input)
    print(f"    Shape: {adata.shape}")

    if args.sample_col in adata.obs.columns:
        adata.obs['sample'] = adata.obs[args.sample_col].astype(str)
    elif 'sample' not in adata.obs.columns:
        adata.obs['sample'] = 'unknown'

    if args.celltype_col in adata.obs.columns:
        adata.obs['celltype_1st'] = adata.obs[args.celltype_col].map(CELLTYPE_MAP).fillna('doublet')
        adata.obs['final_annotation'] = adata.obs[args.celltype_col].astype(str)

    for col, default in [('age', 'NA'), ('sex', 'NA')]:
        if col in adata.obs.columns:
            adata.obs[col] = adata.obs[col].astype(str).replace('nan', default)
        elif 'gender' in adata.obs.columns and col == 'sex':
            adata.obs['sex'] = adata.obs['gender'].astype(str).replace('nan', default)

    if not args.skip_subsampling and adata.n_obs > args.n_target:
        print(f"[2] Stratified subsampling to {args.n_target} ...")
        if 'celltype_1st' in adata.obs.columns:
            vc = adata.obs['celltype_1st'].value_counts()
            selected_idx = []
            for ct, n in vc.items():
                n_sample = max(int(n * args.n_target / adata.n_obs), 100)
                n_sample = min(n_sample, n)
                idx = adata.obs.index[adata.obs['celltype_1st'] == ct].to_numpy()
                chosen = np.random.choice(idx, size=n_sample, replace=False)
                selected_idx.extend(chosen)
            adata = adata[selected_idx].copy()
        else:
            n_sub = min(args.n_target, adata.n_obs)
            selected = np.random.choice(adata.obs_names, size=n_sub, replace=False)
            adata = adata[selected].copy()
        gc.collect()
    print(f"    After subsampling: {adata.shape}")

    print("[3] QC ...")
    adata.var['mt'] = adata.var_names.str.startswith('MT-')
    adata.var['hb'] = adata.var_names.str.contains(r'^HB[^(P)]')
    adata.var['rp'] = adata.var_names.str.match(r'^RP[SL][0-9]')
    sc.pp.calculate_qc_metrics(adata, qc_vars=['mt', 'rp'], percent_top=None, log1p=False, inplace=True)
    if 'pct_counts_mt' in adata.obs.columns:
        adata = adata[adata.obs['pct_counts_mt'] < 20, :]
    sc.pp.filter_genes(adata, min_cells=3)
    sc.pp.filter_cells(adata, min_genes=200)
    print(f"    After QC: {adata.shape}")

    print("[4] Normalize + HVG ...")
    if 'counts' not in adata.layers:
        adata.layers['counts'] = adata.X.copy()
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    sc.pp.highly_variable_genes(adata, n_top_genes=args.hvg_n, flavor='seurat',
                                batch_key='sample' if 'sample' in adata.obs.columns else None)
    rm = (adata.var_names.str.match(r'^MT-') |
          adata.var_names.str.match(r'^RP[SL]') |
          adata.var_names.str.match(r'^[A-Z][A-Z][0-9].*\.[0-9]') |
          adata.var_names.str.match(r'(^LOC|LINC)[1-9]*'))
    adata.var.loc[rm, 'highly_variable'] = False
    n_hvg = adata.var['highly_variable'].sum()
    print(f"    HVG: {n_hvg}")
    hvg_keep = adata.var_names[adata.var['highly_variable']].tolist()
    pd.DataFrame(hvg_keep, columns=['hvg']).to_csv(os.path.join(args.output, 'CIMA_hvg_keep.csv'), index=False)

    print("[5] Subset to HVG only ...")
    adata = adata[:, adata.var['highly_variable']].copy()
    gc.collect()
    print(f"    {adata.shape}")

    print("[6] PCA (skip scale for numpy compat) ...")
    sc.tl.pca(adata, n_comps=50, zero_center=False)

    if not args.skip_harmony and args.batch_key and args.batch_key in adata.obs.columns:
        print(f"[7] Harmony (key={args.batch_key}) ...")
        try:
            sc.external.pp.harmony_integrate(adata, args.batch_key)
            use_rep = 'X_pca_harmony'
        except Exception as e:
            print(f"    Harmony failed: {e}. Using X_pca.")
            use_rep = 'X_pca'
    else:
        print("[7] Skipping Harmony ...")
        use_rep = 'X_pca'

    print("[8] Neighbors + UMAP + Leiden ...")
    sc.pp.neighbors(adata, n_neighbors=30, n_pcs=min(19, adata.obsm['X_pca'].shape[1]-1), use_rep=use_rep)
    sc.tl.umap(adata, min_dist=0.3)
    sc.tl.leiden(adata, resolution=args.resolution, n_iterations=2,
                key_added='leiden_r1.5_n2', flavor='igraph', directed=False)
    print(f"    Clusters: {adata.obs['leiden_r1.5_n2'].nunique()}")

    print("[9] Annotation ...")
    # Side legend (like Step2); avoid legend_loc='on data' which overlays labels on clusters
    sc.settings.set_figure_params(dpi=120, dpi_save=300)
    plot_kw = dict(legend_loc='right margin', frameon=False, show=False)
    if 'celltype_1st' in adata.obs.columns:
        for ext in ('png', 'pdf'):
            sc.pl.umap(adata, color='celltype_1st', save=f'_celltype_1st.{ext}', **plot_kw)
    else:
        adata.obs['celltype_1st'] = adata.obs['leiden_r1.5_n2'].astype(str)
        print("    Warning: No cell type column. Using Leiden IDs. Annotate manually.")
    for ext in ('png', 'pdf'):
        sc.pl.umap(adata, color='leiden_r1.5_n2', save=f'_leiden.{ext}', **plot_kw)


    print("[10] Save + Lineage split ...")
    out_file = os.path.join(args.output, 'CIMA_Annotation_1st.h5ad')
    adata.write_h5ad(out_file)
    print(f"    Saved: {out_file} ({os.path.getsize(out_file)/1e6:.0f}MB)")

    if 'celltype_1st' in adata.obs.columns:
        for name, types in LINEAGES.items():
            mask = adata.obs['celltype_1st'].isin(types)
            if mask.sum() > 0:
                sub = adata[mask].copy()
                sub_file = os.path.join(args.output, f'CIMA_{name}.h5ad')
                sub.write_h5ad(sub_file)
                print(f"    {name}: {sub.n_obs} cells -> {sub_file}")
                del sub; gc.collect()

    del adata; gc.collect()
    print(f"\nDone ({(time.time()-t0)/60:.1f}min)")

if __name__ == '__main__':
    main()
