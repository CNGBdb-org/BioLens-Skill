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

  # 多轮：先看模糊簇，再剔除或细分
  python3 cima_cell_annotation_cpu.py \\
    --input CIMA_TNK_subclustered.h5ad \\
    --output ./step2_r2/ \\
    --lineage TNK \\
    --input-is-lineage \\
    --exclude-clusters 2,5 \\
    --resolution 1.2
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
    map_celltype_1st_to_l1,
    marker_gene_coverage,
    resolve_ontology,
)
from cima_annotation_refine import (  # noqa: E402
    apply_forced_labels,
    export_ambiguous_clusters,
    find_cluster_key,
    parse_cluster_list,
    parse_relabel_map,
)
from cima_annotation_transfer import transfer_labels  # noqa: E402

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
    p.add_argument("--resolution", type=float, default=None, help="Leiden resolution (default 1.0; small 0.8)")
    p.add_argument("--n-pcs", type=int, default=None, help="Number of PCs for neighbors (default 15; small 10)")
    p.add_argument(
        "--profile",
        choices=["auto", "large", "small"],
        default="auto",
        help="auto: few samples/cells → small (skip Harmony, fewer PCs)",
    )
    p.add_argument(
        "--sweep-resolutions",
        default=None,
        help="Comma-separated resolutions to sweep, e.g. 0.4,0.8,1.0,1.2; writes sweep_summary.csv",
    )
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
        "--marker-table",
        default=None,
        help="User marker CSV/TSV (label + markers, or positive/negative)",
    )
    p.add_argument(
        "--marker-mode",
        choices=["builtin", "custom", "merge"],
        default="builtin",
        help="builtin=TrueBlood only; custom=only user table; merge=override/add into TrueBlood",
    )
    p.add_argument(
        "--merge-output",
        action="store_true",
        help="Also write merged CIMA_scRNA_Annotation.h5ad across lineages",
    )
    # Multi-round refinement
    p.add_argument(
        "--input-is-lineage",
        action="store_true",
        help="Input is a previous lineage subclustered h5ad (skip lineage filter)",
    )
    p.add_argument(
        "--cluster-key",
        default=None,
        help="Existing leiden column for refine/exclude/relabel (default: auto)",
    )
    p.add_argument(
        "--ambiguous-margin",
        type=float,
        default=0.05,
        help="Flag clusters whose median annotation_margin < this (export CSV)",
    )
    p.add_argument(
        "--exclude-clusters",
        default=None,
        help="Comma-separated prior clusters to hold out as Ambiguous (or relabel)",
    )
    p.add_argument(
        "--refine-clusters",
        default=None,
        help="Comma-separated prior clusters to re-subcluster at --resolution and re-annotate",
    )
    p.add_argument(
        "--relabel-map",
        default=None,
        help="Force labels: '2:Doublet,5:Unknown' or CSV with cluster,label",
    )
    p.add_argument(
        "--held-out-label",
        default="Ambiguous",
        help="Label for --exclude-clusters cells not covered by --relabel-map",
    )
    p.add_argument(
        "--method",
        choices=["signature", "transfer"],
        default="signature",
        help="signature=TrueBlood/custom markers; transfer=reference h5ad kNN mapping",
    )
    p.add_argument(
        "--reference",
        default=None,
        help="Reference h5ad with known labels (required for --method transfer)",
    )
    p.add_argument(
        "--reference-label",
        default=None,
        help="obs column on reference (default: cell_type_l4 / final_annotation / …)",
    )
    p.add_argument(
        "--transfer-backend",
        choices=["knn", "ingest"],
        default="knn",
        help="knn=joint PCA + majority vote (default); ingest=scanpy.tl.ingest",
    )
    p.add_argument("--transfer-k", type=int, default=15, help="kNN neighbors for transfer")
    p.add_argument(
        "--reference-max-cells",
        type=int,
        default=20000,
        help="Subsample reference if larger (memory cap)",
    )
    return p.parse_args()


def _parse_float_list(text: str | None) -> list[float]:
    if not text:
        return []
    out = []
    for tok in text.replace(";", ",").split(","):
        tok = tok.strip()
        if tok:
            out.append(float(tok))
    return out


def apply_annotation_profile(args, adata) -> str:
    """Fill resolution/n_pcs and maybe skip_harmony for small cohorts."""
    n_obs = adata.n_obs
    sample_key = args.batch_key if args.batch_key in adata.obs.columns else (
        "sample" if "sample" in adata.obs.columns else (
            "sample_id" if "sample_id" in adata.obs.columns else None
        )
    )
    n_samples = int(adata.obs[sample_key].astype(str).nunique()) if sample_key else 1
    profile = args.profile
    reasons = []
    if profile == "auto":
        if n_samples < 100 or n_obs < 8000:
            profile = "small"
            reasons.append(f"n_samples={n_samples}, n_obs={n_obs}")
        else:
            profile = "large"
    if profile == "small":
        if args.resolution is None:
            args.resolution = 0.8
        if args.n_pcs is None:
            args.n_pcs = 10
        if n_samples < 50:
            args.skip_harmony = True
        print(f"  Annotation profile=small ({'; '.join(reasons) or 'explicit'})")
    else:
        if args.resolution is None:
            args.resolution = 1.0
        if args.n_pcs is None:
            args.n_pcs = 15
        print(f"  Annotation profile=large")
    return profile


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


def _stringify_label_cols(adata):
    for col in [
        "cell_type_l1",
        "cell_type_l2",
        "cell_type_l3",
        "cell_type_l4",
        "custom_label",
        "annotation_leaf",
        "parent_cluster",
        "refine_cluster",
    ]:
        if col in adata.obs.columns:
            adata.obs[col] = (
                adata.obs[col].astype(object).where(adata.obs[col].notna(), "").astype(str)
            )
    for col in ("annotation_score", "annotation_margin"):
        if col in adata.obs.columns:
            adata.obs[col] = pd.to_numeric(adata.obs[col], errors="coerce")


def _cluster_and_annotate(sub, args, out_dir, lineage_name, onto, force_l1=None, tag=""):
    """Leiden cluster + marker signature annotate. Returns (adata, leiden_key).

    If args.sweep_resolutions is set, embed once, score each resolution, pick the
    one with highest median annotation_margin (n_clusters in [3, 40]), and write
    `{lineage}_sweep_summary.csv`.
    """
    _ensure_lognorm_for_scoring(sub)
    sub_full = sub.copy()

    batch_key = args.batch_key if args.batch_key in sub.obs.columns else None
    n_hvg = 1500 if getattr(args, "profile_resolved", "large") == "small" else 2500
    sc.pp.highly_variable_genes(
        sub, n_top_genes=min(n_hvg, sub.n_vars), flavor="seurat", batch_key=batch_key
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

    n_comps = min(30 if getattr(args, "profile_resolved", "large") == "small" else 50,
                  sub_hvg.n_obs - 1, sub_hvg.n_vars - 1)
    sc.tl.pca(sub_hvg, n_comps=max(2, n_comps), zero_center=False)

    use_rep = "X_pca"
    if not args.skip_harmony and batch_key:
        try:
            sc.external.pp.harmony_integrate(sub_hvg, batch_key)
            use_rep = "X_pca_harmony"
        except Exception as e:
            print(f"  Harmony failed: {e}")

    n_pcs = min(args.n_pcs, sub_hvg.obsm["X_pca"].shape[1] - 1)
    n_neighbors = 15 if getattr(args, "profile_resolved", "large") == "small" else 30
    sc.pp.neighbors(
        sub_hvg,
        n_neighbors=min(n_neighbors, max(2, sub_hvg.n_obs - 1)),
        n_pcs=max(1, n_pcs),
        use_rep=use_rep,
    )
    sc.tl.umap(sub_hvg, min_dist=0.3)

    sweep = _parse_float_list(getattr(args, "sweep_resolutions", None))
    if args.resolution not in sweep:
        # ensure primary resolution is evaluated
        resolutions = sorted(set(sweep + [float(args.resolution)]))
    else:
        resolutions = sorted(set(sweep)) if sweep else [float(args.resolution)]

    suffix = f"{tag}_" if tag else ""
    prefer = "celltype_1st" if "celltype_1st" in sub_full.obs.columns else None
    if force_l1:
        prefer = None
    mode = getattr(args, "marker_mode", "builtin")

    # Transfer embedding first
    sub_full.obsm["X_pca"] = sub_hvg.obsm["X_pca"]
    if "X_pca_harmony" in sub_hvg.obsm:
        sub_full.obsm["X_pca_harmony"] = sub_hvg.obsm["X_pca_harmony"]
    sub_full.obsm["X_umap"] = sub_hvg.obsm["X_umap"]

    sweep_rows = []
    best = None  # (median_margin, -abs(n_clusters-12), resolution, leiden_key)

    for res in resolutions:
        leiden_key = f"leiden_{suffix}r{res}".replace("__", "_") if tag else f"leiden_r{res}"
        sc.tl.leiden(
            sub_hvg,
            resolution=res,
            n_iterations=2,
            key_added=leiden_key,
            flavor="igraph",
            directed=False,
        )
        n_cl = int(sub_hvg.obs[leiden_key].nunique())
        sub_full.obs[leiden_key] = sub_hvg.obs[leiden_key].values
        print(f"  Clusters ({leiden_key}): {n_cl}")

        # annotate on a view copy of labels only — work on sub_full slice logic
        tmp = sub_full.copy()
        tmp.obs[leiden_key] = sub_full.obs[leiden_key].values
        print(f"  Scoring marker signatures ({mode}) @ r={res} ...")
        annotate_adata(
            tmp,
            cluster_key=leiden_key,
            onto=onto,
            prefer_l1_from=prefer,
            min_margin=args.min_margin,
            force_l1=force_l1,
        )
        label_col = "custom_label" if "custom_label" in tmp.obs else "cell_type_l4"
        margins = pd.to_numeric(tmp.obs.get("annotation_margin"), errors="coerce")
        med = float(margins.median()) if margins is not None and margins.notna().any() else float("nan")
        n_labels = int(tmp.obs[label_col].astype(str).nunique()) if label_col in tmp.obs else 0
        n_amb = int((margins < getattr(args, "ambiguous_margin", 0.05)).sum()) if margins is not None else 0
        sweep_rows.append(
            {
                "resolution": res,
                "leiden_key": leiden_key,
                "n_clusters": n_cl,
                "n_labels": n_labels,
                "median_margin": med,
                "mean_margin": float(margins.mean()) if margins is not None else np.nan,
                "n_cells_low_margin": n_amb,
            }
        )
        # stash per-resolution labels for inspection
        for col in ("cell_type_l4", "custom_label", "annotation_leaf", "annotation_margin", "annotation_score"):
            if col in tmp.obs.columns:
                sub_full.obs[f"{col}_r{res}"] = tmp.obs[col].values

        score = (med if med == med else -1.0, -abs(n_cl - 12), res)
        # Prefer resolutions with a sensible cluster count
        if 3 <= n_cl <= 40:
            cand = (med if med == med else -1.0, -abs(n_cl - 12), res, leiden_key, tmp)
        else:
            cand = (med if med == med else -1.0, -100 - abs(n_cl - 12), res, leiden_key, tmp)
        if best is None or cand[:3] > best[:3]:
            best = cand

    assert best is not None
    chosen_res, leiden_key, chosen_tmp = best[2], best[3], best[4]
    if len(resolutions) > 1:
        summary = pd.DataFrame(sweep_rows).sort_values("resolution")
        summary["chosen"] = summary["resolution"] == chosen_res
        sum_path = os.path.join(out_dir, f"{lineage_name}_sweep_summary.csv")
        summary.to_csv(sum_path, index=False)
        print(f"  Sweep chose resolution={chosen_res} (median_margin={best[0]:.4f}) → {sum_path}")
        print(summary.to_string(index=False))

    # Promote chosen annotation columns to canonical names
    sub = chosen_tmp
    sub.obs[leiden_key] = sub_full.obs[leiden_key].values
    # keep other sweep columns from sub_full
    for col in sub_full.obs.columns:
        if col.endswith(tuple(f"_r{r}" for r in resolutions)) or col.startswith("leiden_"):
            if col not in sub.obs.columns:
                sub.obs[col] = sub_full.obs[col].values
    sub.obsm["X_pca"] = sub_full.obsm["X_pca"]
    if "X_pca_harmony" in sub_full.obsm:
        sub.obsm["X_pca_harmony"] = sub_full.obsm["X_pca_harmony"]
    sub.obsm["X_umap"] = sub_full.obsm["X_umap"]

    # DEG only for chosen resolution
    try:
        sc.tl.rank_genes_groups(sub_hvg, groupby=leiden_key, method="wilcoxon")
        for ext in ("png", "pdf"):
            sc.pl.rank_genes_groups(
                sub_hvg, n_genes=20, show=False, save=f"_{lineage_name}_{suffix}deg.{ext}"
            )
        result = pd.DataFrame(sub_hvg.uns["rank_genes_groups"]["names"])
        result.to_csv(
            os.path.join(out_dir, f"{lineage_name}_{suffix}marker_genes.csv".replace("__", "_")),
            index=False,
        )
    except Exception as e:
        print(f"  rank_genes_groups skipped: {e}")

    try:
        import cosg

        cosg.cosg(sub_hvg, key_added="cosg", mu=1, n_genes_user=50, groupby=leiden_key)
        pd.DataFrame(sub_hvg.uns["cosg"]["names"]).to_csv(
            os.path.join(out_dir, f"{lineage_name}_{suffix}cosg_markers.csv".replace("__", "_")),
            index=False,
        )
    except ImportError:
        print("  COSG not installed (optional)")
    except Exception as e:
        print(f"  COSG skipped: {e}")

    del sub_hvg
    gc.collect()
    # Record chosen resolution for downstream
    args.resolution = float(chosen_res)
    return sub, leiden_key


def subcluster_lineage(adata, lineage_name, args, out_dir, onto, force_l1=None):
    """Subcluster one lineage and assign L1–L4 labels (supports multi-round refine)."""
    t0 = time.time()
    print(f"\n{'=' * 60}")
    print(f"Annotating lineage: {lineage_name}")
    print(f"{'=' * 60}")

    exclude = parse_cluster_list(args.exclude_clusters)
    refine = parse_cluster_list(args.refine_clusters)
    relabel = parse_relabel_map(args.relabel_map)
    if exclude and refine:
        overlap = set(exclude) & set(refine)
        if overlap:
            print(f"Error: clusters in both --exclude-clusters and --refine-clusters: {sorted(overlap)}")
            return None

    if args.input_is_lineage:
        sub = adata.copy()
        n = sub.n_obs
        print(f"  Using full input as lineage subset ({n} cells)")
    else:
        sub, n = _subset_lineage(adata, lineage_name, onto)
        if n == 0 and any(c.startswith("leiden") for c in adata.obs.columns):
            print(
                f"  Lineage filter empty for {lineage_name}; "
                "input looks like a prior subclustered object → using all cells. "
                "(Pass --input-is-lineage to silence.)"
            )
            sub = adata.copy()
            n = sub.n_obs
        if n == 0:
            print(f"  No cells for {lineage_name}, skipping.")
            return None
    print(f"  Cells: {sub.n_obs}")

    # ----- Reference label transfer (scVI-style mapping, CPU kNN) -----
    if getattr(args, "method", "signature") == "transfer":
        if not args.reference:
            print("Error: --method transfer requires --reference PATH.h5ad")
            return None
        print(f"  Transfer from reference {args.reference} ({args.transfer_backend}) ...")
        if getattr(args, "_reference_adata", None) is None:
            args._reference_adata = sc.read_h5ad(args.reference)
            print(f"  Loaded reference {args._reference_adata.shape}")
        ref = args._reference_adata
        # Prefer same lineage in the reference when L1 exists
        l1s = LINEAGE_FILTER.get(lineage_name)
        if l1s and "cell_type_l1" in ref.obs.columns:
            rmask = ref.obs["cell_type_l1"].astype(str).isin(l1s)
            if int(rmask.sum()) >= 20:
                print(f"  Reference subset by L1 {l1s}: {int(rmask.sum())} cells")
                ref = ref[rmask].copy()
        try:
            xfer = transfer_labels(
                sub,
                ref,
                label_col=args.reference_label,
                backend=args.transfer_backend,
                k=args.transfer_k,
                n_pcs=args.n_pcs or 30,
                max_ref_cells=args.reference_max_cells,
            )
        except (ValueError, KeyError) as e:
            print(f"Error: transfer failed: {e}")
            return None
        raw = pd.Series(xfer["labels"], index=sub.obs_names)
        sub.obs["custom_label"] = raw.astype(str).values
        sub.obs["annotation_score"] = xfer["score"]
        sub.obs["annotation_margin"] = xfer["margin"]
        mapped = _match_existing_to_ontology(raw, onto)
        for col in mapped.columns:
            if col in ("annotation_score", "annotation_margin"):
                continue
            sub.obs[col] = mapped[col].values
        # Keep transfer confidence, not NaNs from ontology map
        sub.obs["annotation_score"] = xfer["score"]
        sub.obs["annotation_margin"] = xfer["margin"]
        # Light Leiden on transferred embedding for plots / ambiguous export
        leiden_key = f"leiden_r{args.resolution}"
        if "X_pca" in sub.obsm:
            try:
                sc.pp.neighbors(
                    sub,
                    n_neighbors=min(15, sub.n_obs - 1),
                    n_pcs=min(args.n_pcs or 15, sub.obsm["X_pca"].shape[1]),
                    use_rep="X_pca",
                )
                if "X_umap" not in sub.obsm:
                    sc.tl.umap(sub, min_dist=0.3)
                sc.tl.leiden(
                    sub,
                    resolution=args.resolution,
                    n_iterations=2,
                    key_added=leiden_key,
                    flavor="igraph",
                    directed=False,
                )
            except Exception as e:
                print(f"  post-transfer Leiden skipped: {e}")
                leiden_key = None
        print(
            f"  Transfer stats: {xfer['stats']}  "
            f"(label={xfer['label_col']})"
        )
        return _finalize_lineage(sub, lineage_name, out_dir, leiden_key, t0, args)

    # ----- Round-2: relabel only -----
    if relabel and not exclude and not refine and not args.use_existing_annotation:
        try:
            prev_key = find_cluster_key(sub, args.cluster_key, args.resolution)
        except ValueError as e:
            print(f"Error: {e}")
            return None
        n_chg = apply_forced_labels(sub, cluster_key=prev_key, relabel=relabel)
        print(f"  Relabeled {n_chg} cells via --relabel-map on {prev_key}")
        leiden_key = prev_key
        return _finalize_lineage(sub, lineage_name, out_dir, leiden_key, t0, args)

    # ----- Round-2: refine selected prior clusters -----
    if refine:
        try:
            prev_key = find_cluster_key(sub, args.cluster_key, None)
        except ValueError as e:
            print(f"Error: {e}")
            return None
        parent = sub
        parent.obs["parent_cluster"] = parent.obs[prev_key].astype(str)
        mask = parent.obs[prev_key].astype(str).isin(refine)
        n_ref = int(mask.sum())
        if n_ref == 0:
            print(f"Error: --refine-clusters {refine} matched 0 cells in {prev_key}")
            return None
        print(f"  Refining {n_ref} cells from clusters {refine} (key={prev_key})")
        piece = parent[mask].copy()
        piece, new_key = _cluster_and_annotate(
            piece, args, out_dir, lineage_name, onto, force_l1=force_l1, tag="refine"
        )
        # merge labels back
        for col in [
            "cell_type_l1",
            "cell_type_l2",
            "cell_type_l3",
            "cell_type_l4",
            "custom_label",
            "annotation_leaf",
        ]:
            if col not in piece.obs.columns:
                continue
            if col not in parent.obs.columns:
                parent.obs[col] = ""
            if pd.api.types.is_categorical_dtype(parent.obs[col]):
                parent.obs[col] = parent.obs[col].astype(object)
            parent.obs.loc[mask, col] = piece.obs[col].astype(str).values
        for col in ("annotation_score", "annotation_margin"):
            if col not in piece.obs.columns:
                continue
            if col not in parent.obs.columns:
                parent.obs[col] = np.nan
            parent.obs[col] = pd.to_numeric(parent.obs[col], errors="coerce")
            parent.obs.loc[mask, col] = pd.to_numeric(piece.obs[col], errors="coerce").values
        if "refine_cluster" not in parent.obs.columns:
            parent.obs["refine_cluster"] = ""
        parent.obs["refine_cluster"] = parent.obs["refine_cluster"].astype(object)
        parent.obs.loc[mask, "refine_cluster"] = piece.obs[new_key].astype(str).values
        if relabel:
            apply_forced_labels(parent, cluster_key=prev_key, relabel=relabel)
        return _finalize_lineage(parent, lineage_name, out_dir, prev_key, t0, args)

    # ----- Round-2: exclude fuzzy clusters then recluster remainder -----
    held = None
    if exclude:
        try:
            prev_key = find_cluster_key(sub, args.cluster_key, None)
        except ValueError as e:
            print(f"Error: {e}")
            return None
        mask_ex = sub.obs[prev_key].astype(str).isin(exclude)
        n_ex = int(mask_ex.sum())
        print(f"  Excluding {n_ex} cells from clusters {exclude} (key={prev_key})")
        held = sub[mask_ex].copy()
        # default Ambiguous, override with relabel map
        held_map = {c: args.held_out_label for c in exclude}
        held_map.update({k: v for k, v in relabel.items() if k in set(exclude)})
        apply_forced_labels(held, cluster_key=prev_key, relabel=held_map)
        held.obs["parent_cluster"] = held.obs[prev_key].astype(str)
        sub = sub[~mask_ex].copy()
        if sub.n_obs < 10:
            print("Error: too few cells left after exclude")
            return None

    if args.use_existing_annotation and args.celltype_col in sub.obs.columns:
        print(f"  Using existing annotation from '{args.celltype_col}' (ontology map)")
        mapped = _match_existing_to_ontology(sub.obs[args.celltype_col], onto)
        for col in mapped.columns:
            sub.obs[col] = mapped[col].values
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
        sub, leiden_key = _cluster_and_annotate(
            sub, args, out_dir, lineage_name, onto, force_l1=force_l1
        )

    if held is not None:
        # align columns and concat held-out ambiguous cells
        for col in sub.obs.columns:
            if col not in held.obs.columns:
                held.obs[col] = pd.NA
        for col in held.obs.columns:
            if col not in sub.obs.columns:
                sub.obs[col] = pd.NA
        try:
            sub = sc.concat([sub, held], join="outer", index_unique=None)
        except TypeError:
            sub = sub.concatenate(held, join="outer", index_unique=None)
        print(f"  Re-attached held-out cells → total {sub.n_obs}")

    return _finalize_lineage(sub, lineage_name, out_dir, leiden_key, t0, args)


def _finalize_lineage(sub, lineage_name, out_dir, leiden_key, t0, args):
    label_col = "custom_label" if "custom_label" in sub.obs else "cell_type_l4"
    if label_col in sub.obs:
        vc = sub.obs[label_col].astype(str).value_counts()
        print(f"  Labels via {label_col} ({vc.shape[0]}):")
        for k, v in vc.head(12).items():
            print(f"    {k}: {v}")
        if vc.shape[0] > 12:
            print(f"    ... ({vc.shape[0] - 12} more)")

    sc.settings.set_figure_params(dpi=120, dpi_save=300)
    plot_cols = [
        c for c in ["cell_type_l1", "cell_type_l2", "cell_type_l4", "custom_label"] if c in sub.obs
    ]
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
    _stringify_label_cols(sub)
    sub.write_h5ad(out_file)
    cols = [
        c
        for c in [
            "cell_type_l1",
            "cell_type_l2",
            "cell_type_l3",
            "cell_type_l4",
            "custom_label",
            "annotation_leaf",
            "annotation_score",
            "annotation_margin",
            leiden_key,
            "parent_cluster",
            "refine_cluster",
            "celltype_1st",
            "custom_label",
        ]
        if c and c in sub.obs.columns
    ]
    sub.obs[cols].to_csv(os.path.join(out_dir, f"{lineage_name}_l1_l4_assignments.csv"))

    if leiden_key and leiden_key in sub.obs and "annotation_margin" in sub.obs.columns:
        amb_path = os.path.join(out_dir, f"{lineage_name}_ambiguous_clusters.csv")
        summary = export_ambiguous_clusters(
            sub.obs,
            cluster_key=leiden_key,
            out_path=amb_path,
            margin_thresh=args.ambiguous_margin,
            label_col=label_col if label_col in sub.obs.columns else "cell_type_l4",
        )
        n_amb = int(summary["ambiguous"].sum())
        print(
            f"  Ambiguous clusters (median margin < {args.ambiguous_margin}): "
            f"{n_amb}/{len(summary)} → {amb_path}"
        )
        if n_amb:
            show = summary.loc[summary["ambiguous"], ["cluster", "n_cells", "median_margin", "top_label"]]
            print(show.head(8).to_string(index=False))

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

    try:
        onto, force_l1 = resolve_ontology(
            marker_table=args.marker_table,
            marker_mode=args.marker_mode,
            ontology_path=args.ontology,
        )
    except (ValueError, FileNotFoundError) as e:
        print(f"Error: {e}")
        return

    print(
        f"Ontology: {onto['n_nodes']} nodes, {onto['n_leaves']} leaves, "
        f"kind={onto.get('source_kind', 'builtin')}, L1={onto.get('l1_lineages')}"
    )
    if onto.get("merge_stats"):
        print(f"  merge: {onto['merge_stats']}")
    if force_l1:
        print(f"  custom flat mode → force L1={force_l1}")

    if getattr(args, "method", "signature") == "transfer" and not args.reference:
        print("Error: --method transfer requires --reference PATH.h5ad")
        return

    print(f"Reading {args.input} ...")
    adata = sc.read_h5ad(args.input)
    print(f"  Shape: {adata.shape}")

    args.profile_resolved = apply_annotation_profile(args, adata)

    cov = marker_gene_coverage(adata, onto)
    print(
        f"  Marker coverage: pos {cov['present_pos']}/{cov['leaf_markers_pos']}, "
        f"neg {cov['present_neg']}/{cov['leaf_markers_neg']}, "
        f"missing_genes={cov['n_missing']}"
    )
    if cov["n_missing"] and args.marker_mode != "builtin":
        preview = ", ".join(cov["missing_genes"][:12])
        print(f"  Missing marker genes (first): {preview}")

    if "celltype_1st" not in adata.obs.columns and "cell_type_l1" not in adata.obs.columns:
        print("Error: need 'celltype_1st' (Step1) or 'cell_type_l1'. Run cima-scrna-preprocessing first.")
        return

    # Global L1 pre-label for subsetting (refine inside each lineage after log-norm)
    if "cell_type_l1" not in adata.obs.columns:
        if "celltype_1st" in adata.obs.columns:
            adata.obs["cell_type_l1"] = map_celltype_1st_to_l1(adata.obs["celltype_1st"]).values
        else:
            adata.obs["cell_type_l1"] = "unknown"

    if args.input_is_lineage and args.lineage == "all":
        print("Error: --input-is-lineage requires a concrete --lineage (not all)")
        return

    lineages = (
        ["B_cells", "myeloid", "TNK", "CD4T", "CD8T", "NK"]
        if args.lineage == "all"
        else [args.lineage]
    )
    # Avoid double-processing T when all: do TNK once covering CD4/CD8/NK; still allow CD4T etc. alone
    if args.lineage == "all":
        lineages = ["B_cells", "myeloid", "TNK"]

    # Multi-round flags only make sense on a single lineage pass
    if (args.exclude_clusters or args.refine_clusters or args.relabel_map) and len(lineages) > 1:
        print("Error: --exclude/--refine/--relabel require a single --lineage")
        return

    written = []
    for lineage in lineages:
        path = subcluster_lineage(
            adata, lineage, args, args.output, onto, force_l1=force_l1
        )
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

    print("\n✅ Cell annotation done.")
    print(
        "Outputs: *_subclustered.h5ad, *_l1_l4_assignments.csv, "
        "*_ambiguous_clusters.csv, figures/umap_*_*.pdf"
    )


if __name__ == "__main__":
    main()
