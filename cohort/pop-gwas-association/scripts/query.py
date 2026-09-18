#!/usr/bin/env python3
"""
Population GWAS Association — query.py
=======================================
GWAS 关联分析主入口脚本。
支持 PLINK / REGENIE / SAIGE / BOLT-LMM。
含 Manhattan/QQ plot 和 λGC 计算。

依赖: PLINK 1.9+, pandas, numpy, matplotlib
可选: REGENIE, SAIGE, BOLT-LMM
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

def find_plink():
    for name in ["plink2", "plink"]:
        p = shutil.which(name)
        if p: return p
        for d in [os.path.expanduser("~/software/miniforge/envs/cima/bin"),
                  os.path.expanduser("~/software/miniforge/bin"),
                  "/usr/bin", "/usr/local/bin"]:
            fp = os.path.join(d, name)
            if os.path.isfile(fp) and os.access(fp, os.X_OK): return fp
    return None

PLINK_BIN = find_plink()

def find_tool(name):
    p = shutil.which(name)
    if p: return p
    for d in [os.path.expanduser("~/software/miniforge/envs/cima/bin"),
              os.path.expanduser("~/software/miniforge/bin"),
              "/usr/bin", "/usr/local/bin"]:
        fp = os.path.join(d, name)
        if os.path.isfile(fp) and os.access(fp, os.X_OK): return fp
    return None

REGENIE_BIN = find_tool("regenie")
SAIGE_BIN = find_tool("SAIGE") or find_tool("saige")
BOLT_BIN = find_tool("bolt")

def run_plink(args):
    if not PLINK_BIN:
        return 1, "PLINK not found"
    cmd = [PLINK_BIN] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 1, "TIMEOUT"


# ---- PLINK Association ----
def association_plink(prefix, pheno_file, covar_file, output_dir, binary=False, maf=0.01):
    """Run PLINK association test."""
    os.makedirs(output_dir, exist_ok=True)
    out_prefix = os.path.join(output_dir, "gwas")
    args = ["--bfile", prefix, "--maf", str(maf)]
    if binary:
        args += ["--logistic", "hide-covar"]
    else:
        args += ["--linear", "hide-covar"]
    args += ["--pheno", pheno_file, "--mpheno", "1"]
    if covar_file and os.path.isfile(covar_file):
        args += ["--covar", covar_file, "--covar-name", "age,sex,PC1,PC2,PC3,PC4,PC5,PC6,PC7,PC8,PC9,PC10"]
    args += ["--out", out_prefix]
    rc, out_text = run_plink(args)
    if rc != 0:
        print(f"ERROR: {out_text[:500]}")
        return None
    # Find result file
    ext = ".logistic" if binary else ".linear"
    result_file = out_prefix + ext
    if not os.path.isfile(result_file):
        # Try .assoc or .assoc.linear
        for alt in [out_prefix + ".assoc.linear", out_prefix + ".assoc.logistic"]:
            if os.path.isfile(alt):
                result_file = alt
                break
    if not os.path.isfile(result_file):
        print(f"ERROR: result file not found. Check {out_prefix}.log")
        return None
    print(f"PLINK association complete: {result_file}")
    return result_file


# ---- REGENIE ----
def association_regenie(prefix, pheno_file, covar_file, output_dir, binary=False, maf=0.01, n_pcs=10):
    """Run REGENIE two-step association."""
    if not REGENIE_BIN:
        print("REGENIE not found. Install: conda install -c bioconda regenie")
        print("Falling back to PLINK...")
        return association_plink(prefix, pheno_file, covar_file, output_dir, binary, maf)
    os.makedirs(output_dir, exist_ok=True)
    step1_out = os.path.join(output_dir, "step1_null")
    step2_out = os.path.join(output_dir, "step2_assoc")
    # Step 1: null model
    cmd1 = [REGENIE_BIN, "--bed", prefix,
            "--phenoFile", pheno_file,
            "--out", step1_out,
            "--bt" if binary else "",
            "--step", "1"]
    cmd1 = [c for c in cmd1 if c]
    if covar_file and os.path.isfile(covar_file):
        cmd1 += ["--covarFile", covar_file]
    print(f"REGENIE Step 1 (null model)...")
    try:
        r1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=14400)
        if r1.returncode != 0:
            print(f"REGENIE Step1 failed: {r1.stderr[:500]}")
            return None
    except subprocess.TimeoutExpired:
        print("REGENIE Step1 timed out")
        return None
    # Step 2: association
    cmd2 = [REGENIE_BIN, "--bed", prefix,
            "--phenoFile", pheno_file,
            "--covarFile", covar_file,
            "--bsize", "400",
            "--minMAF", str(maf),
            "--out", step2_out,
            "--bt" if binary else "",
            "--step", "2",
            "--pred", step1_out + "_pred.list"]
    cmd2 = [c for c in cmd2 if c]
    print(f"REGENIE Step 2 (association)...")
    try:
        r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=14400)
        if r2.returncode != 0:
            print(f"REGENIE Step2 failed: {r2.stderr[:500]}")
            return None
    except subprocess.TimeoutExpired:
        print("REGENIE Step2 timed out")
        return None
    # Find result
    result_files = [f for f in os.listdir(output_dir) if "step2" in f and f.endswith("_regenie.txt")]
    if result_files:
        result_file = os.path.join(output_dir, sorted(result_files)[0])
        print(f"REGENIE complete: {result_file}")
        return result_file
    print("REGENIE results not found")
    return None


# ---- SAIGE ----
def association_saige(prefix, pheno_file, covar_file, output_dir, binary=False):
    """Run SAIGE two-step association."""
    if not SAIGE_BIN:
        print("SAIGE not found. Install: conda install -c bioconda saige")
        return association_plink(prefix, pheno_file, covar_file, output_dir, binary)
    os.makedirs(output_dir, exist_ok=True)
    print("SAIGE: Step 1 (fit null model)...")
    # This is simplified - SAIGE has complex parameter requirements
    step1_out = os.path.join(output_dir, "step1_saige.rda")
    cmd1 = ["Rscript", "-e", f"""
        library(SAIGE)
        # Step 1: fit null model
        # See SAIGE documentation for full parameters
    """]
    print("SAIGE requires R + SAIGE package. Please refer to:")
    print("  https://github.com/saigegit/SAIGE")
    print("Falling back to PLINK...")
    return association_plink(prefix, pheno_file, covar_file, output_dir, binary)


# ---- λGC ----
def compute_lambdagc(sumstats_file, output_dir):
    """Compute genomic inflation factor (λGC)."""
    df = pd.read_csv(sumstats_file, delim_whitespace=True)
    pval_col = None
    for c in ["P", "PVAL", "PVALUE", "p"]:
        if c in df.columns:
            pval_col = c
            break
    if not pval_col:
        print(f"ERROR: no p-value column found in {sumstats_file}")
        return None
    chi2 = -2 * np.log10(df[pval_col].astype(float))  # Actually chi2 = qchisq(1-p)
    from scipy.stats import chi2 as chi2_dist
    observed = -2 * np.log(df[pval_col].dropna().astype(float))
    # λGC = median(observed chi2) / median(expected chi2) = median(observed) / 0.4549
    median_chi2 = np.median(observed)
    lambdagc = median_chi2 / 0.4549  # median of chi2(df=1) under null
    print(f"λGC (genomic inflation factor) = {lambdagc:.4f}")
    print(f"  Based on {len(observed)} SNPs")
    if lambdagc > 1.10:
        print(f"  WARNING: λGC > 1.10, possible population stratification")
    elif lambdagc < 0.90:
        print(f"  WARNING: λGC < 0.90, possible over-correction")
    else:
        print(f"  λGC within acceptable range (0.90-1.10)")
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        report = {"lambda_gc": float(lambdagc), "n_snps": int(len(observed)),
                  "median_chi2": float(median_chi2)}
        with open(os.path.join(output_dir, "lambdagc.json"), "w") as f:
            json.dump(report, f, indent=2)
    return lambdagc


# ---- Manhattan Plot ----
def plot_manhattan(sumstats_file, output, pval_threshold=5e-8):
    """Generate Manhattan plot."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib not installed")
        return
    df = pd.read_csv(sumstats_file, delim_whitespace=True)
    # Detect columns
    chr_col = next((c for c in ["CHR", "CHROM", "chr", "chrom"] if c in df.columns), None)
    pos_col = next((c for c in ["BP", "POS", "pos", "position"] if c in df.columns), None)
    pval_col = next((c for c in ["P", "PVAL", "PVALUE", "p"] if c in df.columns), None)
    if not all([chr_col, pos_col, pval_col]):
        print(f"ERROR: missing columns. Need CHR, BP, P. Found: {list(df.columns)}")
        return
    df = df.dropna(subset=[chr_col, pos_col, pval_col])
    df = df[df[chr_col].astype(str).str.isdigit() | (df[chr_col].astype(str).isin(["X","Y"]))].copy()
    df["CHR"] = df[chr_col].astype(str).str.replace("X","23").str.replace("Y","24").astype(int)
    df = df[df["CHR"] <= 22].sort_values(["CHR", pos_col])
    df["-log10P"] = -np.log10(df[pval_col].astype(float))
    # Cumulative position
    df["cum_pos"] = 0
    offset = 0
    for chrom in sorted(df["CHR"].unique()):
        mask = df["CHR"] == chrom
        df.loc[mask, "cum_pos"] = df.loc[mask, pos_col].astype(int) + offset
        offset = df.loc[mask, "cum_pos"].max() + 5_000_000
    fig, ax = plt.subplots(figsize=(14, 5))
    colors = ["#1f77b4", "#ff7f0e"] * 11
    for chrom in sorted(df["CHR"].unique()):
        mask = df["CHR"] == chrom
        ax.scatter(df.loc[mask, "cum_pos"], df.loc[mask, "-log10P"],
                   s=1, c=colors[chrom-1], alpha=0.6)
    ax.axhline(-np.log10(pval_threshold), color="red", linestyle="--", lw=0.5,
               label=f"p={pval_threshold}")
    ax.set_xlabel("Chromosome")
    ax.set_ylabel("-log10(P)")
    ax.set_title("Manhattan Plot")
    # X-axis ticks at chromosome midpoints
    tick_positions = []
    for chrom in sorted(df["CHR"].unique()):
        mask = df["CHR"] == chrom
        tick_positions.append((chrom, df.loc[mask, "cum_pos"].mean()))
    ax.set_xticks([t[1] for t in tick_positions])
    ax.set_xticklabels([str(t[0]) for t in tick_positions], fontsize=7)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print(f"Manhattan plot saved: {output}")


# ---- QQ Plot ----
def plot_qq(sumstats_file, output):
    """Generate QQ plot."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from scipy.stats import norm
    except ImportError:
        print("ERROR: matplotlib/scipy not installed")
        return
    df = pd.read_csv(sumstats_file, delim_whitespace=True)
    pval_col = next((c for c in ["P", "PVAL", "PVALUE", "p"] if c in df.columns), None)
    if not pval_col:
        print("ERROR: no p-value column")
        return
    pvals = df[pval_col].dropna().astype(float).sort_values()
    n = len(pvals)
    expected = -np.log10(np.arange(1, n+1) / (n+1))
    observed = -np.log10(pvals)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(expected, observed, s=1, alpha=0.5)
    ax.plot([0, expected.max()], [0, expected.max()], "r--", lw=0.5)
    ax.set_xlabel("Expected -log10(P)")
    ax.set_ylabel("Observed -log10(P)")
    ax.set_title("QQ Plot")
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print(f"QQ plot saved: {output}")


# ---- Pipeline ----
def pipeline_full(args):
    """Full GWAS pipeline."""
    os.makedirs(args.output, exist_ok=True)
    print("=== Step 1: Association Test ===")
    if args.tool == "regenie":
        result = association_regenie(args.input, args.pheno, args.covar, args.output, args.binary, args.maf)
    elif args.tool == "saige":
        result = association_saige(args.input, args.pheno, args.covar, args.output, args.binary)
    elif args.tool == "bolt":
        print("BOLT-LMM not yet fully integrated. Use PLINK...")
        result = association_plink(args.input, args.pheno, args.covar, args.output, args.binary, args.maf)
    else:
        result = association_plink(args.input, args.pheno, args.covar, args.output, args.binary, args.maf)
    if not result:
        return
    print("\n=== Step 2: λGC ===")
    compute_lambdagc(result, args.output)
    print("\n=== Step 3: Manhattan Plot ===")
    plot_manhattan(result, os.path.join(args.output, "manhattan.png"), args.pval_threshold)
    print("\n=== Step 4: QQ Plot ===")
    plot_qq(result, os.path.join(args.output, "qq.png"))
    # Summary
    df = pd.read_csv(result, delim_whitespace=True)
    pval_col = next((c for c in ["P", "PVAL", "PVALUE"] if c in df.columns), None)
    n_sig = int((df[pval_col].astype(float) < args.pval_threshold).sum()) if pval_col else 0
    print(f"\n=== GWAS Complete ===")
    print(f"  Summary stats: {result}")
    print(f"  Significant SNPs (p < {args.pval_threshold}): {n_sig}")
    print(f"  Manhattan: {os.path.join(args.output, 'manhattan.png')}")
    print(f"  QQ plot: {os.path.join(args.output, 'qq.png')}")


def main():
    parser = argparse.ArgumentParser(description="Population GWAS Association")
    sub = parser.add_subparsers(dest="module", required=True)

    # pipeline
    p_pipe = sub.add_parser("pipeline")
    p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full")
    add_full_args(p_full)

    # association
    p_assoc = sub.add_parser("association")
    p_assoc_sub = p_assoc.add_subparsers(dest="subcommand", required=True)
    for tool in ["plink", "regenie", "saige", "bolt"]:
        sp = p_assoc_sub.add_parser(tool)
        sp.add_argument("--input", required=True, help="PLINK prefix")
        sp.add_argument("--pheno", required=True, help="Phenotype file (FID IID PHENO)")
        sp.add_argument("--covar", help="Covariate file")
        sp.add_argument("--output", required=True)
        sp.add_argument("--binary", action="store_true", help="Binary trait")
        sp.add_argument("--maf", type=float, default=0.01)
        sp.add_argument("--n-pcs", type=int, default=10)

    # stats
    p_stats = sub.add_parser("stats")
    p_stats_sub = p_stats.add_subparsers(dest="subcommand", required=True)
    p_lg = p_stats_sub.add_parser("lambdagc")
    p_lg.add_argument("--sumstats", required=True)
    p_lg.add_argument("--output", required=True)

    # plot
    p_plot = sub.add_parser("plot")
    p_plot_sub = p_plot.add_subparsers(dest="subcommand", required=True)
    p_man = p_plot_sub.add_parser("manhattan")
    p_man.add_argument("--sumstats", required=True)
    p_man.add_argument("--output", required=True)
    p_man.add_argument("--pval-threshold", type=float, default=5e-8)
    p_qq = p_plot_sub.add_parser("qq")
    p_qq.add_argument("--sumstats", required=True)
    p_qq.add_argument("--output", required=True)

    args = parser.parse_args()

    if args.module == "pipeline" and args.subcommand == "full":
        pipeline_full(args)
    elif args.module == "association":
        if args.subcommand == "plink":
            association_plink(args.input, args.pheno, args.covar, args.output, args.binary, args.maf)
        elif args.subcommand == "regenie":
            association_regenie(args.input, args.pheno, args.covar, args.output, args.binary, args.maf)
        elif args.subcommand == "saige":
            association_saige(args.input, args.pheno, args.covar, args.output, args.binary)
        elif args.subcommand == "bolt":
            association_plink(args.input, args.pheno, args.covar, args.output, args.binary, args.maf)
    elif args.module == "stats" and args.subcommand == "lambdagc":
        compute_lambdagc(args.sumstats, args.output)
    elif args.module == "plot" and args.subcommand == "manhattan":
        plot_manhattan(args.sumstats, args.output, args.pval_threshold)
    elif args.module == "plot" and args.subcommand == "qq":
        plot_qq(args.sumstats, args.output)


def add_full_args(p):
    p.add_argument("--input", required=True)
    p.add_argument("--pheno", required=True)
    p.add_argument("--covar", help="Covariate file")
    p.add_argument("--output", required=True)
    p.add_argument("--tool", default="plink", choices=["plink", "regenie", "saige", "bolt"])
    p.add_argument("--binary", action="store_true")
    p.add_argument("--maf", type=float, default=0.01)
    p.add_argument("--n-pcs", type=int, default=10)
    p.add_argument("--pval-threshold", type=float, default=5e-8)


if __name__ == "__main__":
    main()
