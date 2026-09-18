#!/usr/bin/env python3
"""
Population Structure PCA — query.py
===================================
群体结构分析主入口脚本。
LD 剪枝 → PCA → 聚类 → 离群检测 → 可视化。

依赖: PLINK 1.9+, pandas, numpy, sklearn, matplotlib
"""
import argparse
import os
import sys
import shutil
import subprocess
import json
from pathlib import Path

import numpy as np
import pandas as pd

# ---- PLINK detection (reuse) ----
def find_plink():
    for name in ["plink2", "plink"]:
        p = shutil.which(name)
        if p:
            return p
        for d in [
            os.path.expanduser("~/software/miniforge/envs/cima/bin"),
            os.path.expanduser("~/software/miniforge/bin"),
            "/usr/bin", "/usr/local/bin",
        ]:
            fp = os.path.join(d, name)
            if os.path.isfile(fp) and os.access(fp, os.X_OK):
                return fp
    return None

PLINK_BIN = find_plink()

def run_plink(args):
    if not PLINK_BIN:
        print("ERROR: PLINK not found. Install: conda install -c bioconda plink")
        return 1, ""
    cmd = [PLINK_BIN] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 1, "TIMEOUT"


# ---- LD Pruning ----
def ld_prune(prefix, output_dir, window=50, step=5, r2=0.2):
    """LD pruning to get independent SNPs for PCA."""
    out = os.path.join(output_dir, "ld_prune")
    rc, out_text = run_plink([
        "--bfile", prefix,
        "--indep-pairwise", f"{window}", f"{step}", str(r2),
        "--out", out,
    ])
    if rc != 0:
        print(f"ERROR in LD pruning: {out_text}")
        return None
    pruned_file = out + ".prune.in"
    n_pruned = sum(1 for _ in open(pruned_file)) if os.path.isfile(pruned_file) else 0
    print(f"LD pruning: {n_pruned} independent SNPs kept (window={window}, step={step}, r2={r2})")
    return out + ".prune.in"


# ---- PCA ----
def compute_pca(prefix, output_dir, n_pcs=10, extract_file=None):
    """Compute PCA using PLINK --pca."""
    out = os.path.join(output_dir, "pca")
    args = [
        "--bfile", prefix,
        "--pca", str(n_pcs), "header-w",
        "--out", out,
    ]
    if extract_file and os.path.isfile(extract_file):
        args = [
            "--bfile", prefix,
            "--extract", extract_file,
            "--pca", str(n_pcs), "header-w",
            "--out", out,
        ]
    rc, out_text = run_plink(args)
    if rc != 0:
        print(f"ERROR in PCA: {out_text}")
        return None, None
    eigenval_file = out + ".eigenval"
    eigenvec_file = out + ".eigenvec"
    if not os.path.isfile(eigenvec_file):
        print(f"ERROR: eigenvec file not found: {eigenvec_file}")
        return None, None
    eigenval = pd.read_csv(eigenval_file, delim_whitespace=True, header=None)
    eigenvec = pd.read_csv(eigenvec_file, delim_whitespace=True)
    print(f"PCA: {n_pcs} PCs computed for {len(eigenvec)} samples")
    print(f"Top 5 eigenvalues:\n{eigenval.head(5)}")
    return eigenval, eigenvec


# ---- Clustering ----
def cluster_samples(eigenvec_file, n_clusters=3, output_dir="."):
    """KMeans clustering on PC1-PC10."""
    try:
        from sklearn.cluster import KMeans
    except ImportError:
        print("ERROR: sklearn not installed. pip install scikit-learn")
        return None
    df = pd.read_csv(eigenvec_file, delim_whitespace=True)
    pc_cols = [c for c in df.columns if c.startswith("PC")]
    X = df[pc_cols].values
    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["cluster"] = km.fit_predict(X)
    out_file = os.path.join(output_dir, "cluster_labels.csv")
    df[["FID", "IID"] + pc_cols + ["cluster"]].to_csv(out_file, index=False)
    cluster_counts = df["cluster"].value_counts().sort_index()
    print(f"KMeans clustering ({n_clusters} clusters):")
    for c, n in cluster_counts.items():
        print(f"  Cluster {c}: {n} samples")
    print(f"Labels saved: {out_file}")
    return df


# ---- Outlier Detection ----
def detect_outliers(eigenvec_file, sd_threshold=6, output_dir="."):
    """Detect samples that are outliers in PC space (mean ± N*SD)."""
    df = pd.read_csv(eigenvec_file, delim_whitespace=True)
    pc_cols = [c for c in df.columns if c.startswith("PC")]
    outliers = []
    for pc in pc_cols:
        mean = df[pc].mean()
        std = df[pc].std()
        outlier_idx = df[(df[pc] - mean).abs() > sd_threshold * std].index
        for idx in outlier_idx:
            outliers.append({"IID": df.loc[idx, "IID"], "PC": pc,
                            "value": df.loc[idx, pc], "mean": mean, "sd": std})
    outlier_df = pd.DataFrame(outliers)
    unique_outliers = outlier_df["IID"].unique() if len(outlier_df) > 0 else []
    print(f"Outlier detection (|z| > {sd_threshold}): {len(unique_outliers)} unique outlier samples")
    if len(outlier_df) > 0:
        out_file = os.path.join(output_dir, "pc_outliers.csv")
        outlier_df.to_csv(out_file, index=False)
        print(f"Outlier list saved: {out_file}")
    return outlier_df


# ---- Visualization ----
def plot_pca(eigenvec_file, eigenval_file, output, pc_x=1, pc_y=2, cluster_file=None):
    """Scatter plot of PC1 vs PC2."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib not installed. pip install matplotlib")
        return
    eigenvec = pd.read_csv(eigenvec_file, delim_whitespace=True)
    pc_cols = [c for c in eigenvec.columns if c.startswith("PC")]

    # eigenvalues for explained variance
    ev = pd.read_csv(eigenval_file, delim_whitespace=True, header=None)
    total_var = ev[0].sum()
    pct_x = ev.iloc[pc_x - 1, 0] / total_var * 100 if len(ev) >= pc_x else 0
    pct_y = ev.iloc[pc_y - 1, 0] / total_var * 100 if len(ev) >= pc_y else 0

    fig, ax = plt.subplots(figsize=(8, 6))
    if cluster_file and os.path.isfile(cluster_file):
        clusters = pd.read_csv(cluster_file)
        eigenvec = eigenvec.merge(clusters[["IID", "cluster"]], on="IID", how="left")
        for c in sorted(eigenvec["cluster"].dropna().unique()):
            mask = eigenvec["cluster"] == c
            ax.scatter(eigenvec.loc[mask, f"PC{pc_x}"],
                       eigenvec.loc[mask, f"PC{pc_y}"], s=5, label=f"Cluster {c}", alpha=0.6)
        ax.legend(fontsize=8)
    else:
        ax.scatter(eigenvec[f"PC{pc_x}"], eigenvec[f"PC{pc_y}"], s=5, alpha=0.6)
    ax.set_xlabel(f"PC{pc_x} ({pct_x:.1f}% variance)")
    ax.set_ylabel(f"PC{pc_y} ({pct_y:.1f}% variance)")
    ax.set_title("Population Structure PCA")
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print(f"PCA plot saved: {output}")


# ---- Pipeline ----
def pipeline_full(args):
    """Full structure analysis: LD prune → PCA → cluster → outlier → plot."""
    os.makedirs(args.output, exist_ok=True)
    # 1. LD pruning
    print("=== Step 1: LD Pruning ===")
    prune_file = ld_prune(args.input, args.output, args.window, args.step, args.r2)
    # 2. PCA
    print("\n=== Step 2: PCA ===")
    eigenval, eigenvec = compute_pca(args.input, args.output, args.n_pcs, prune_file)
    if eigenvec is None:
        return
    eigenvec_file = os.path.join(args.output, "pca.eigenvec")
    eigenval_file = os.path.join(args.output, "pca.eigenval")
    # 3. Clustering
    print("\n=== Step 3: Clustering ===")
    cluster_df = cluster_samples(eigenvec_file, args.n_clusters, args.output)
    # 4. Outlier detection
    print("\n=== Step 4: Outlier Detection ===")
    detect_outliers(eigenvec_file, args.sd, args.output)
    # 5. Plot
    print("\n=== Step 5: Visualization ===")
    cluster_file = os.path.join(args.output, "cluster_labels.csv")
    plot_pca(eigenvec_file, eigenval_file,
             os.path.join(args.output, "pca_scatter.png"), cluster_file=cluster_file)
    print(f"\n=== Pipeline Complete ===")
    print(f"Results: {args.output}")
    print(f"  eigenvalues: {eigenval_file}")
    print(f"  eigenvectors: {eigenvec_file}")
    print(f"  clusters: {cluster_file}")
    print(f"  plot: {os.path.join(args.output, 'pca_scatter.png')}")


# ---- Main ----
def main():
    parser = argparse.ArgumentParser(description="Population Structure PCA")
    sub = parser.add_subparsers(dest="module", required=True)

    # pipeline
    p_pipe = sub.add_parser("pipeline", help="Full pipeline")
    p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full", help="Full analysis")
    add_full_args(p_full)

    # ld
    p_ld = sub.add_parser("ld", help="LD pruning")
    p_ld_sub = p_ld.add_subparsers(dest="subcommand", required=True)
    p_prune = p_ld_sub.add_parser("prune", help="LD pruning")
    p_prune.add_argument("--input", required=True, help="PLINK prefix")
    p_prune.add_argument("--output", required=True)
    p_prune.add_argument("--window", type=int, default=50)
    p_prune.add_argument("--step", type=int, default=5)
    p_prune.add_argument("--r2", type=float, default=0.2)

    # pca
    p_pca = sub.add_parser("pca", help="PCA computation")
    p_pca_sub = p_pca.add_subparsers(dest="subcommand", required=True)
    p_compute = p_pca_sub.add_parser("compute", help="Compute PCA")
    p_compute.add_argument("--input", required=True, help="PLINK prefix")
    p_compute.add_argument("--output", required=True)
    p_compute.add_argument("--n-pcs", type=int, default=10)
    p_compute.add_argument("--extract", help="SNP list for PCA (e.g. prune.in)")

    # cluster
    p_cl = sub.add_parser("cluster", help="Clustering")
    p_cl_sub = p_cl.add_subparsers(dest="subcommand", required=True)
    p_km = p_cl_sub.add_parser("kmeans", help="KMeans clustering")
    p_km.add_argument("--eigenvec", required=True, help="eigenvec file")
    p_km.add_argument("--n-clusters", type=int, default=3)
    p_km.add_argument("--output", required=True)

    # outlier
    p_out = sub.add_parser("outlier", help="Outlier detection")
    p_out_sub = p_out.add_subparsers(dest="subcommand", required=True)
    p_det = p_out_sub.add_parser("detect", help="Detect outliers")
    p_det.add_argument("--eigenvec", required=True)
    p_det.add_argument("--output", required=True)
    p_det.add_argument("--sd", type=float, default=6.0)

    # plot
    p_plot = sub.add_parser("plot", help="Visualization")
    p_plot_sub = p_plot.add_subparsers(dest="subcommand", required=True)
    p_sc = p_plot_sub.add_parser("scatter", help="PCA scatter plot")
    p_sc.add_argument("--eigenvec", required=True)
    p_sc.add_argument("--eigenval", required=True)
    p_sc.add_argument("--output", required=True)
    p_sc.add_argument("--pc-x", type=int, default=1)
    p_sc.add_argument("--pc-y", type=int, default=2)
    p_sc.add_argument("--cluster-file", help="cluster labels CSV")

    args = parser.parse_args()

    if args.module == "pipeline" and args.subcommand == "full":
        pipeline_full(args)
    elif args.module == "ld" and args.subcommand == "prune":
        ld_prune(args.input, args.output, args.window, args.step, args.r2)
    elif args.module == "pca" and args.subcommand == "compute":
        compute_pca(args.input, args.output, args.n_pcs, args.extract)
    elif args.module == "cluster" and args.subcommand == "kmeans":
        cluster_samples(args.eigenvec, args.n_clusters, args.output)
    elif args.module == "outlier" and args.subcommand == "detect":
        detect_outliers(args.eigenvec, args.sd, args.output)
    elif args.module == "plot" and args.subcommand == "scatter":
        plot_pca(args.eigenvec, args.eigenval, args.output, args.pc_x, args.pc_y, args.cluster_file)


def add_full_args(p):
    p.add_argument("--input", required=True, help="PLINK prefix (QC'd)")
    p.add_argument("--output", required=True, help="Output directory")
    p.add_argument("--n-pcs", type=int, default=10)
    p.add_argument("--window", type=int, default=50)
    p.add_argument("--step", type=int, default=5)
    p.add_argument("--r2", type=float, default=0.2)
    p.add_argument("--sd", type=float, default=6.0)
    p.add_argument("--n-clusters", type=int, default=3)


if __name__ == "__main__":
    if not PLINK_BIN:
        print("WARNING: PLINK not found. Install: conda install -c bioconda plink")
    main()
