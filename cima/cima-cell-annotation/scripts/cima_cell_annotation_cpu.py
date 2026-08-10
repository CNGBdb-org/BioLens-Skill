#!/usr/bin/env python3
"""
CIMA 细胞亚群 L1–L4 分层注释（CPU）

基于 TrueBlood CellType marker 层级本体
(https://db.cngb.org/trueblood/cima/cellType)：
  1) 按系群子集 / 可选 Leiden 子聚类
  2) 用 +/- marker 签名给 cluster 打分
  3) 写出 cell_type_l1..l4（73 个 leaf ≈ 门户 L4）

用法:
  python3 cima_cell_annotation_cpu.py \\
    --input /path/to/CIMA_Annotation_1st.h5ad \\
    --output /path/to/output/ \\
    --lineage all \\
    --resolution 1.0
"""
from __future__ import annotations

import argparse
import gc
import os
import sys
import time

import numpy as np
import pandas as pd
import scanpy as sc

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from cima_annotation_ontology import (  # noqa: E402
    LINEAGE_FILTER,
    annotate_adata,
    assign_l1,
    load_ontology,
    map_celltype_1st_to_l1,
)

# Step1 lineage split keys → celltype_1st values (legacy)
LEGACY_LINEAGES = {
    "B_cells": ["Naive B", "Memory B", "Plasma&Cycling T"],
    "myeloid": ["pDC", "cDC", "cMono", "ncMono", "Megakaryocyte", "HSPC"],
    "TNK": ["T cells", "NK cells"],
    "erythrocyte": ["Erythrocyte"],
}


def parse_args():
    p = argparse.ArgumentParser(description="CIMA Cell Annotation L1–L4 (CPU)")
    p.add_argument("--input", required=True, help="Input h5ad (CIMA_Annotation_1st)")
    p.add_argument("--output", required=True, help="Output directory")
    p.add_argument(
        "--lineage",
        default="all",
        choices=["all", "B_cells", "myeloid", "TNK", "CD4T", "CD8T", "NK"],
        help="Which lineage to annotate",
    )
    p.add_argument("--resolution", type=float, default=1.0, help="Leiden resolution")
    p.add_argument("--n-pcs", type=int, default=15, help="Number of PCs for neighbors")
    p.add_argument(
        "--use-existing-annotation",
        action="store_true",
        help="Skip re-clustering; map existing labels into l1–l4 when possible",
    )
    p.add_argument(
        "--celltype-col",
        default="final_annotation",
        help="Existing annotation column (with --use-existing-annotation)",
    )
    p.add_argument("--skip-harmony", action="store_true", help="Skip Harmony")
    p.add_argument("--batch-key", default="sample", help="Batch key for Harmony")
    p.add_argument(
        "--min-margin",
        type=float,
        default=0.0,
        help="Minimum score margin (best−second) when assigning leaf labels",
    )
    p.add_argument(
        "--ontology",
        default=None,
        help="Optional path to cima_celltype_ontology.json",
    )
    p.add_argument(
        "--merge-output",
        action="store_true",
        help="Also write merged CIMA_scRNA_Annotation.h5ad across lineages",
    )
    return p.parse_args()


def _ensure_lognorm_for_scoring(sub):
    """Lightweight normalize for marker scoring if counts layer present."""
    if "counts" in sub.layers:
        sub.X = sub.layers["counts"].copy()
        sc.pp.normalize_total(sub, target_sum=1e4)
        sc.pp.log1p(sub)
    return sub


def _subset_lineage(adata, lineage_name, onto):
    """Subset by L1 (preferred) or legacy celltype_1st."""
    if "cell_type_l1" in adata.obs.columns:
        l1s = LINEAGE_FILTER.get(lineage_name)
        if l1s:
            mask = adata.obs["cell_type_l1"].isin(l1s)
            return adata[mask].copy(), mask.sum()

    # Prefer mapping celltype_1st → L1 then filter
    if "celltype_1st" in adata.obs.columns:
        l1_mapped = map_celltype_1st_to_l1(adata.obs["celltype_1st"])
        l1s = LINEAGE_FILTER.get(lineage_name)
        if l1s:
            mask = l1_mapped.isin(l1s)
            # TNK / T cells: also include via legacy list
            if lineage_name in LEGACY_LINEAGES:
                mask = mask | adata.obs["celltype_1st"].isin(LEGACY_LINEAGES[lineage_name])
            return adata[mask].copy(), int(mask.sum())

    types = LEGACY_LINEAGES.get(lineage_name, [lineage_name])
    mask = adata.obs["celltype_1st"].isin(types) if "celltype_1st" in adata.obs.columns else np.zeros(adata.n_obs, dtype=bool)
    return adata[mask].copy(), int(mask.sum())


def _match_existing_to_ontology(labels: pd.Series, onto: dict) -> pd.DataFrame:
    """Map free-text labels to ontology nodes by name / id / alias."""
    alias = {k: v for k, v in (onto.get("alias_to_canonical") or {}).items()}
    by_name = {n["name"]: n for n in onto["nodes"]}
    by_id = {n["id"]: n for n in onto["nodes"]}
    # case-insensitive
    by_name_ci = {n["name"].lower(): n for n in onto["nodes"]}

    rows = []
    for lab in labels.astype(str):
        key = alias.get(lab, lab)
        node = by_name.get(key) or by_id.get(key) or by_name_ci.get(key.lower())
        if node is None:
            rows.append(
                {
                    "cell_type_l1": pd.NA,
                    "cell_type_l2": pd.NA,
                    "cell_type_l3": pd.NA,
                    "cell_type_l4": lab,
                    "annotation_leaf": lab,
                    "annotation_score": np.nan,
                    "annotation_margin": np.nan,
                }
            )
        else:
            path = node.get("path") or [node["name"]]
            rows.append(
                {
                    "cell_type_l1": path[0] if path else pd.NA,
                    "cell_type_l2": path[1] if len(path) > 1 else pd.NA,
                    "cell_type_l3": path[2] if len(path) > 2 else pd.NA,
                    "cell_type_l4": node.get("cell_type_l4") or node["name"],
                    "annotation_leaf": node["name"],
                    "annotation_score": np.nan,
                    "annotation_margin": np.nan,
                }
            )
    return pd.DataFrame(rows, index=labels.index)


def subcluster_lineage(adata, lineage_name, args, out_dir, onto):
    """Subcluster one lineage and assign L1–L4 labels."""
    t0 = time.time()
    print(f"\n{'=' * 60}")
    print(f"Annotating lineage: {lineage_name}")
    print(f"{'=' * 60}")

    sub, n = _subset_lineage(adata, lineage_name, onto)
    if n == 0:
        print(f"  No cells for {lineage_name}, skipping.")
        return None
    print(f"  Cells: {sub.n_obs}")

    if args.use_existing_annotation and args.celltype_col in sub.obs.columns:
        print(f"  Using existing annotation from '{args.celltype_col}' (ontology map)")
        mapped = _match_existing_to_ontology(sub.obs[args.celltype_col], onto)
        for col in mapped.columns:
            sub.obs[col] = mapped[col].values
        # Ensure L1 present for plotting
        if sub.obs["cell_type_l1"].isna().all():
            sub.obs["cell_type_l1"] = assign_l1(sub, onto=onto).values
        if "X_pca" not in sub.obsm:
            _ensure_lognorm_for_scoring(sub)
            sc.pp.highly_variable_genes(sub, n_top_genes=min(2000, sub.n_vars), flavor="seurat")
            hv = sub[:, sub.var["highly_variable"]].copy() if "highly_variable" in sub.var else sub
            sc.tl.pca(hv, n_comps=min(50, hv.n_obs - 1, hv.n_vars - 1), zero_center=False)
            sub.obsm["X_pca"] = hv.obsm["X_pca"]
        if "X_umap" not in sub.obsm:
            sc.pp.neighbors(
                sub,
                n_neighbors=min(15, sub.n_obs - 1),
                n_pcs=min(args.n_pcs, sub.obsm["X_pca"].shape[1] - 1),
            )
            sc.tl.umap(sub, min_dist=0.3)
        leiden_key = None
    else:
        # Keep full-gene matrix for marker scoring; cluster on HVGs only
        _ensure_lognorm_for_scoring(sub)
        sub_full = sub.copy()

        batch_key = args.batch_key if args.batch_key in sub.obs.columns else None
        sc.pp.highly_variable_genes(
            sub, n_top_genes=min(2500, sub.n_vars), flavor="seurat", batch_key=batch_key
        )
        rm = (
            sub.var_names.str.match(r"^MT-")
            | sub.var_names.str.match(r"^RP[SL]")
            | sub.var_names.str.match(r"^[A-Z][A-Z][0-9].*\.[0-9]")
            | sub.var_names.str.match(r"(^LOC|LINC)[1-9]*")
        )
        if "highly_variable" in sub.var.columns:
            sub.var.loc[rm, "highly_variable"] = False
            sub_hvg = sub[:, sub.var["highly_variable"]].copy()
        else:
            sub_hvg = sub
        gc.collect()

        n_comps = min(50, sub_hvg.n_obs - 1, sub_hvg.n_vars - 1)
        sc.tl.pca(sub_hvg, n_comps=max(2, n_comps), zero_center=False)

        use_rep = "X_pca"
        if not args.skip_harmony and batch_key:
            try:
                sc.external.pp.harmony_integrate(sub_hvg, batch_key)
                use_rep = "X_pca_harmony"
            except Exception as e:
                print(f"  Harmony failed: {e}")

        n_pcs = min(args.n_pcs, sub_hvg.obsm["X_pca"].shape[1] - 1)
        sc.pp.neighbors(
            sub_hvg,
            n_neighbors=min(30, sub_hvg.n_obs - 1),
            n_pcs=max(1, n_pcs),
            use_rep=use_rep,
        )
        sc.tl.umap(sub_hvg, min_dist=0.3)
        leiden_key = f"leiden_r{args.resolution}"
        sc.tl.leiden(
            sub_hvg,
            resolution=args.resolution,
            n_iterations=2,
            key_added=leiden_key,
            flavor="igraph",
            directed=False,
        )
        print(f"  Clusters: {sub_hvg.obs[leiden_key].nunique()}")

        # Transfer embeddings / clusters back to full-gene object
        sub_full.obsm["X_pca"] = sub_hvg.obsm["X_pca"]
        if "X_pca_harmony" in sub_hvg.obsm:
            sub_full.obsm["X_pca_harmony"] = sub_hvg.obsm["X_pca_harmony"]
        sub_full.obsm["X_umap"] = sub_hvg.obsm["X_umap"]
        sub_full.obs[leiden_key] = sub_hvg.obs[leiden_key].values
        sub = sub_full

        # Marker DEG helpers (optional; on HVG object)
        try:
            sc.tl.rank_genes_groups(sub_hvg, groupby=leiden_key, method="wilcoxon")
            for ext in ("png", "pdf"):
                sc.pl.rank_genes_groups(
                    sub_hvg, n_genes=20, show=False, save=f"_{lineage_name}_deg.{ext}"
                )
            result = pd.DataFrame(sub_hvg.uns["rank_genes_groups"]["names"])
            result.to_csv(os.path.join(out_dir, f"{lineage_name}_marker_genes.csv"), index=False)
        except Exception as e:
            print(f"  rank_genes_groups skipped: {e}")

        try:
            import cosg

            cosg.cosg(sub_hvg, key_added="cosg", mu=1, n_genes_user=50, groupby=leiden_key)
            pd.DataFrame(sub_hvg.uns["cosg"]["names"]).to_csv(
                os.path.join(out_dir, f"{lineage_name}_cosg_markers.csv"), index=False
            )
        except ImportError:
            print("  COSG not installed (optional)")
        except Exception as e:
            print(f"  COSG skipped: {e}")

        del sub_hvg
        gc.collect()

        # Hierarchical L1–L4 assignment on full gene set
        print("  Scoring TrueBlood marker signatures → L1–L4 ...")
        prefer = "celltype_1st" if "celltype_1st" in sub.obs.columns else None
        annotate_adata(
            sub,
            cluster_key=leiden_key,
            onto=onto,
            prefer_l1_from=prefer,
            min_margin=args.min_margin,
        )

    # Summary
    if "cell_type_l4" in sub.obs:
        vc = sub.obs["cell_type_l4"].astype(str).value_counts()
        print(f"  L4 labels ({vc.shape[0]}):")
        for k, v in vc.head(12).items():
            print(f"    {k}: {v}")
        if vc.shape[0] > 12:
            print(f"    ... ({vc.shape[0] - 12} more)")

    # Plots (side legend; PNG for preview + PDF for publication)
    sc.settings.set_figure_params(dpi=120, dpi_save=300)
    plot_cols = [c for c in ["cell_type_l1", "cell_type_l2", "cell_type_l4"] if c in sub.obs]
    if leiden_key and leiden_key in sub.obs:
        plot_cols = [leiden_key] + plot_cols
    for col in plot_cols:
        for ext in ("png", "pdf"):
            try:
                sc.pl.umap(
                    sub,
                    color=col,
                    save=f"_{lineage_name}_{col}.{ext}",
                    legend_loc="right margin",
                    frameon=False,
                    show=False,
                )
            except Exception as e:
                print(f"  plot {col} ({ext}) failed: {e}")

    out_file = os.path.join(out_dir, f"CIMA_{lineage_name}_subclustered.h5ad")
    sub.write_h5ad(out_file)
    # assignment table
    cols = [
        c
        for c in [
            "cell_type_l1",
            "cell_type_l2",
            "cell_type_l3",
            "cell_type_l4",
            "annotation_leaf",
            "annotation_score",
            "annotation_margin",
            leiden_key,
            "celltype_1st",
        ]
        if c and c in sub.obs.columns
    ]
    sub.obs[cols].to_csv(os.path.join(out_dir, f"{lineage_name}_l1_l4_assignments.csv"))
    print(f"  Saved: {out_file} ({os.path.getsize(out_file) / 1e6:.1f}MB)")
    print(f"  Time: {(time.time() - t0) / 60:.1f}min")
    del sub
    gc.collect()
    return out_file


def main():
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(os.path.join(args.output, "figures"), exist_ok=True)
    sc.settings.figdir = os.path.join(args.output, "figures")
    sc.settings.verbosity = 2
    np.random.seed(66)

    onto = load_ontology(args.ontology)
    print(
        f"Ontology: {onto['n_nodes']} nodes, {onto['n_leaves']} leaves (L4), "
        f"L1={onto.get('l1_lineages')}"
    )

    print(f"Reading {args.input} ...")
    adata = sc.read_h5ad(args.input)
    print(f"  Shape: {adata.shape}")

    if "celltype_1st" not in adata.obs.columns and "cell_type_l1" not in adata.obs.columns:
        print("Error: need 'celltype_1st' (Step1) or 'cell_type_l1'. Run cima-scrna-preprocessing first.")
        return

    # Global L1 pre-label for subsetting (refine inside each lineage after log-norm)
    if "cell_type_l1" not in adata.obs.columns:
        if "celltype_1st" in adata.obs.columns:
            adata.obs["cell_type_l1"] = map_celltype_1st_to_l1(adata.obs["celltype_1st"]).values
        else:
            adata.obs["cell_type_l1"] = "unknown"

    lineages = (
        ["B_cells", "myeloid", "TNK", "CD4T", "CD8T", "NK"]
        if args.lineage == "all"
        else [args.lineage]
    )
    # Avoid double-processing T when all: do TNK once covering CD4/CD8/NK; still allow CD4T etc. alone
    if args.lineage == "all":
        lineages = ["B_cells", "myeloid", "TNK"]

    written = []
    for lineage in lineages:
        path = subcluster_lineage(adata, lineage, args, args.output, onto)
        if path:
            written.append(path)

    if args.merge_output and written:
        print("\nMerging lineage h5ads ...")
        parts = [sc.read_h5ad(p) for p in written]
        try:
            merged = sc.concat(parts, join="outer", index_unique=None)
        except TypeError:
            merged = parts[0].concatenate(parts[1:], join="outer", index_unique=None)
        out_m = os.path.join(args.output, "CIMA_scRNA_Annotation.h5ad")
        merged.write_h5ad(out_m)
        print(f"  Merged: {out_m} ({merged.n_obs} cells)")

    print("\n✅ Cell annotation (L1–L4) done.")
    print("Outputs: *_subclustered.h5ad, *_l1_l4_assignments.csv, figures/umap_*_cell_type_l*.pdf")


if __name__ == "__main__":
    main()
