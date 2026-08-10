#!/usr/bin/env python3
"""CIMA Pseudobulk Aggregation & Variance Partition (CPU)

Groups scRNA counts by sample × celltype, sums to pseudobulk, then runs
OLS variance decomposition: log1p(expression) ~ celltype + covariates.

Usage:
  python3 cima_pseudobulk_variance_cpu.py \
    --input CIMA_Annotation_1st.h5ad \
    --output ./step3_output/ \
    --sample-col sample \
    --celltype-col celltype_1st \
    --covariates age sex
"""
import argparse, os, warnings
import numpy as np
import pandas as pd
import scanpy as sc
import statsmodels.api as sm
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore")


def parse_args():
    p = argparse.ArgumentParser(
        description="CIMA Pseudobulk Aggregation & Variance Partition (CPU)"
    )
    p.add_argument("--input", required=True, help="Input h5ad (CIMA_Annotation_1st)")
    p.add_argument("--output", required=True, help="Output directory")
    p.add_argument("--sample-col", default="sample", help="Sample ID column")
    p.add_argument("--celltype-col", default="celltype_1st", help="Cell type column")
    p.add_argument("--covariates", nargs="+", default=["age", "sex"],
                   help="Covariate columns in .obs (default: age sex)")
    p.add_argument("--chunk-size", type=int, default=1000,
                   help="Gene chunk size for memory")
    p.add_argument("--min-celltype-samples", type=int, default=2,
                   help="Minimum samples per celltype")
    return p.parse_args()


def process_gene_chunk(chunk, groups):
    """Sum raw counts per (celltype, sample) for a gene chunk."""
    return chunk.groupby(groups).sum()


def grouped_obs_sum(adata, group_keys, chunk_size=1000):
    """Chunked pseudobulk aggregation: sum raw counts by group_keys."""
    pseudobulk = pd.DataFrame()
    groups = [adata.obs[key] for key in group_keys]
    for start in range(0, adata.n_vars, chunk_size):
        end = min(start + chunk_size, adata.n_vars)
        chunk = adata[:, start:end].to_df()
        chunk_sum = process_gene_chunk(chunk, groups)
        pseudobulk = pd.concat([pseudobulk, chunk_sum], axis=1)
    return pseudobulk


def variance_partition(log_expr, meta, covariates):
    """OLS: log1p(y) ~ celltype + cov1 + cov2 → R² contributions."""
    celltypes = meta["celltype"].unique()
    all_ct = meta["celltype"].copy()

    results = []
    for gene in log_expr.columns:
        y = log_expr[gene].values
        try:
            # Full model
            X_full = sm.add_constant(
                pd.get_dummies(all_ct, drop_first=True).astype(float)
            )
            for cov in covariates:
                if cov in meta.columns:
                    cov_val = meta[cov]
                    if pd.api.types.is_numeric_dtype(cov_val):
                        cov_val = cov_val.astype(float).values.reshape(-1, 1)
                    else:
                        cov_val = pd.get_dummies(cov_val.astype(str), drop_first=True).astype(float)
                        if cov_val.ndim == 1:
                            cov_val = cov_val.values.reshape(-1, 1)
                        else:
                            cov_val = cov_val.values
                    X_full = np.column_stack([X_full, cov_val])

            model_full = sm.OLS(y, X_full).fit()
            ss_total = np.sum((y - y.mean()) ** 2)

            # Celltype contribution
            X_no_ct = X_full[:, :1]
            offset = 1
            for cov in covariates:
                if cov in meta.columns:
                    if pd.api.types.is_numeric_dtype(meta[cov]):
                        n_cov_cols = 1
                    else:
                        n_cov_cols = max(len(meta[cov].astype(str).unique()) - 1, 1)
                    offset += max(1, n_cov_cols)
            n_ct_cols = X_full.shape[1] - offset
            if n_ct_cols > 0:
                X_no_ct = np.column_stack([X_no_ct, X_full[:, offset:]])
                model_no_ct = sm.OLS(y, X_no_ct).fit()
                ct_r2 = (model_no_ct.ssr - model_full.ssr) / ss_total
            else:
                ct_r2 = 0

            # Covariate contributions
            cov_r2 = {}
            remaining_cols = list(range(1, 1 + n_ct_cols))
            for ci, cov in enumerate(covariates):
                if cov not in meta.columns:
                    cov_r2[cov] = 0
                    continue
                cols_to_drop = []
                start_col = 1 + n_ct_cols + sum(
                    (
                        len(pd.get_dummies(meta[c].astype(str), drop_first=True).columns)
                        if c in meta.columns and not pd.api.types.is_numeric_dtype(meta[c])
                        else 1
                    )
                    for c in covariates[:ci]
                )
                if cov in meta.columns and not pd.api.types.is_numeric_dtype(meta[cov]):
                    n_c = max(len(meta[cov].astype(str).dropna().unique()) - 1, 1)
                else:
                    n_c = 1
                cols_to_drop = list(range(int(start_col), int(start_col + n_c)))
                all_cols = list(range(X_full.shape[1]))
                keep = [c for c in all_cols if c not in cols_to_drop]
                X_reduced = X_full[:, keep]
                model_reduced = sm.OLS(y, X_reduced).fit()
                cov_r2[cov] = (model_reduced.ssr - model_full.ssr) / ss_total

            residual_r2 = 1 - model_full.rsquared

            row = {"gene": gene, "celltype": ct_r2, "residual": residual_r2}
            row.update(cov_r2)
            results.append(row)
        except Exception:
            continue

    df = pd.DataFrame(results)
    if "gene" in df.columns:
        df = df.set_index("gene")
    return df


def main():
    args = parse_args()
    os.makedirs(args.output, exist_ok=True)
    os.makedirs(os.path.join(args.output, "figures"), exist_ok=True)
    sc.settings.figdir = os.path.join(args.output, "figures")
    sc.settings.verbosity = 1
    np.random.seed(42)

    print(f"Loading {args.input}...")
    adata = sc.read_h5ad(args.input)
    print(f"  Cells: {adata.n_obs}, Genes: {adata.n_vars}")

    # Validate columns
    for col in [args.sample_col, args.celltype_col] + args.covariates:
        if col not in adata.obs.columns:
            print(f"  WARNING: column '{col}' not found in .obs")

    # ── Pseudobulk aggregation ──
    print(f"\n[1/3] Pseudobulk aggregation (sample × celltype)...")
    group_keys = [args.sample_col, args.celltype_col]
    pb = grouped_obs_sum(adata, group_keys, args.chunk_size)

    # Clean index
    pb.index = [f"{s}:{c}" for s, c in pb.index]

    # Filter low-sample celltypes
    ct_counts = pd.Series([i.split(":")[1] for i in pb.index]).value_counts()
    keep_ct = ct_counts[ct_counts >= args.min_celltype_samples].index
    pb = pb[[":".join(i.split(":")[1:]) in keep_ct for i in pb.index]]
    print(f"  Pseudobulk shape: {pb.shape} (celltypes ≥ {args.min_celltype_samples} samples)")

    # Metadata
    meta = pd.DataFrame({"barcode": pb.index}, index=pb.index)
    meta["individual"] = [i.split(":")[0] for i in pb.index]
    meta["celltype"] = [i.split(":")[1] for i in pb.index]
    for cov in args.covariates:
        if cov in adata.obs.columns:
            mapping = adata.obs.groupby(args.sample_col)[cov].first()
            meta[cov] = meta["individual"].map(mapping)

    # Save
    pb.to_csv(os.path.join(args.output, "pseudobulk_BySampleCelltype.csv"))
    meta.to_csv(os.path.join(args.output, "pseudobulk_metadata.csv"))
    print(f"  Saved pseudobulk_BySampleCelltype.csv ({pb.shape})")
    print(f"  Saved pseudobulk_metadata.csv")

    # ── Variance partition ──
    print(f"\n[2/3] Variance partition (OLS on log1p)...")
    log_expr = np.log1p(pb.clip(lower=0))

    # Keep expressed genes
    gene_mask = (log_expr > 0.01).sum(axis=0) >= 3
    log_expr = log_expr.loc[:, gene_mask]
    print(f"  Expressed genes: {log_expr.shape[1]}")

    var_df = variance_partition(log_expr, meta, args.covariates)

    var_path = os.path.join(args.output, "varPartResults.csv")
    var_df.to_csv(var_path)
    print(f"  Saved varPartResults.csv ({var_df.shape[0]} genes)")

    # ── Summary figure ──
    print(f"\n[3/3] Summary plot...")
    if len(var_df) == 0:
        print("  No genes passed variance partition — skipping plot.")
    else:
        comps = ["celltype"] + [c for c in args.covariates if c in var_df.columns] + ["residual"]
        available = [c for c in comps if c in var_df.columns]
        if not available:
            print("  No valid variance columns — skipping plot.")
        else:
            medians = var_df[available].median().sort_values(ascending=False)
            fig, ax = plt.subplots(figsize=(8, 4))
            colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"][:len(medians)]
            ax.barh(range(len(medians)), medians.values, color=colors, height=0.6)
            ax.set_yticks(range(len(medians)))
            ax.set_yticklabels(medians.index)
            ax.set_xlabel("Median variance explained")
            ax.set_title("Variance Partition (log1p OLS)")
            ax.invert_yaxis()
            plt.tight_layout()
            fig.savefig(os.path.join(args.output, "figures", "variance_partition.png"), dpi=300, bbox_inches="tight")
            fig.savefig(os.path.join(args.output, "figures", "variance_partition.pdf"), bbox_inches="tight")
            plt.close()
            print(f"  Saved figures/variance_partition.pdf")

    print("\nDone!")
    print(f"  Output: {args.output}/")
    print(f"    pseudobulk_BySampleCelltype.csv  — log1p expression matrix")
    print(f"    pseudobulk_metadata.csv          — sample/celltype metadata")
    print(f"    varPartResults.csv               — variance components per gene")


if __name__ == "__main__":
    main()
