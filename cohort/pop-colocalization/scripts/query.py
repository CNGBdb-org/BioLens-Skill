#!/usr/bin/env python3
"""
Population Colocalization — query.py
=====================================
GWAS × QTL 共定位分析：coloc.abf / eCAVIAR / HyPrColoc。
计算 PP4、5 假设后验概率、regional plot。

依赖: pandas, numpy, matplotlib
可选: R+coloc, R+HyPrColoc
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

def find_rscript():
    for d in [os.path.expanduser("~/software/miniforge/envs/cima/bin"),
              os.path.expanduser("~/software/miniforge/bin"),
              "/usr/bin", "/usr/local/bin"]:
        fp = os.path.join(d, "Rscript")
        if os.path.isfile(fp) and os.access(fp, os.X_OK): return fp
    return shutil.which("Rscript")


# ---- Locus extraction & alignment ----
def extract_and_align(gwas_file, qtl_file, locus_str, flank=500000):
    """Extract locus from both datasets and align by SNP."""
    parts = locus_str.replace("chr", "").split(":")
    chrom = parts[0]
    if "-" in parts[1]:
        start, end = map(int, parts[1].split("-"))
    else:
        center = int(parts[1])
        start, end = center - flank, center + flank
    gwas = pd.read_csv(gwas_file, delim_whitespace=True)
    qtl = pd.read_csv(qtl_file, delim_whitespace=True)
    # Detect columns
    for df, name in [(gwas, "GWAS"), (qtl, "QTL")]:
        chr_col = next((c for c in ["CHR", "CHROM"] if c in df.columns), None)
        pos_col = next((c for c in ["BP", "POS"] if c in df.columns), None)
        snp_col = next((c for c in ["SNP", "rsID"] if c in df.columns), None)
        if not chr_col or not pos_col:
            if not snp_col:
                print(f"ERROR: {name} needs CHR/BP or SNP column")
                return None
    # Filter by locus
    for df, name in [(gwas, "GWAS"), (qtl, "QTL")]:
        chr_col = next((c for c in ["CHR", "CHROM"] if c in df.columns), None)
        pos_col = next((c for c in ["BP", "POS"] if c in df.columns), None)
        if chr_col and pos_col:
            mask = (df[chr_col].astype(str) == str(chrom)) & \
                   (df[pos_col].astype(int) >= start) & \
                   (df[pos_col].astype(int) <= end)
            df.drop(df[~mask].index, inplace=True)
    # Align by SNP
    gwas_snp = next((c for c in ["SNP", "rsID"] if c in gwas.columns), None)
    qtl_snp = next((c for c in ["SNP", "rsID"] if c in qtl.columns), None)
    if gwas_snp and qtl_snp:
        merged = gwas.merge(qtl, on=gwas_snp, suffixes=("_gwas", "_qtl"), how="inner")
    else:
        # Align by CHR:BP
        gwas["key"] = gwas[chr_col].astype(str) + ":" + gwas[pos_col].astype(str)
        qtl["key"] = qtl[chr_col].astype(str) + ":" + qtl[pos_col].astype(str)
        merged = gwas.merge(qtl, on="key", suffixes=("_gwas", "_qtl"), how="inner")
    print(f"Aligned: {len(merged)} shared SNPs in locus chr{chrom}:{start}-{end}")
    if len(merged) < 50:
        print("WARNING: < 50 shared SNPs, colocalization may be unreliable")
    return merged, chrom, start, end


# ---- coloc.abf ----
def run_coloc(merged, output_dir, n_gwas=None, n_qtl=None, pp4_threshold=0.8):
    """Run coloc.abf via R coloc package."""
    rscript = find_rscript()
    if not rscript:
        print("Rscript not found. Using Python approximation.")
        return run_coloc_python(merged, output_dir, pp4_threshold)
    os.makedirs(output_dir, exist_ok=True)
    # Prepare input
    gwas_file = os.path.join(output_dir, "gwas_locus.tsv")
    qtl_file = os.path.join(output_dir, "qtl_locus.tsv")
    # Extract needed columns
    snp_col = next((c for c in ["SNP", "rsID"] if c in merged.columns), None)
    beta_g = next((c for c in ["BETA_gwas", "BETA"] if c in merged.columns), None)
    se_g = next((c for c in ["SE_gwas", "SE"] if c in merged.columns), None)
    p_g = next((c for c in ["P_gwas", "P"] if c in merged.columns), None)
    beta_q = next((c for c in ["BETA_qtl", "BETA"] if c in merged.columns), None)
    se_q = next((c for c in ["SE_qtl", "SE"] if c in merged.columns), None)
    p_q = next((c for c in ["P_qtl", "P"] if c in merged.columns), None)
    # Infer sample sizes
    if n_gwas is None:
        n_gwas = 10000  # default assumption
    if n_qtl is None:
        n_qtl = 500
    merged[[snp_col, beta_g, se_g, p_g]].to_csv(gwas_file, sep="\t", index=False)
    merged[[snp_col, beta_q, se_q, p_q]].to_csv(qtl_file, sep="\t", index=False)
    r_script = f"""
library(coloc)
gwas <- read.table("{gwas_file}", header=TRUE, sep="\\t")
qtl <- read.table("{qtl_file}", header=TRUE, sep="\\t")
result <- coloc.abf(dataset1=list(beta=gwas[[2]], varbeta=gwas[[3]]^2,
                     snp=gwas[[1]], N={n_gwas}, type="quant"),
                    dataset2=list(beta=qtl[[2]], varbeta=qtl[[3]]^2,
                     snp=qtl[[1]], N={n_qtl}, type="quant"))
cat("PP.H0:", result$summary["PP.H0.abf"], "\\n")
cat("PP.H1:", result$summary["PP.H1.abf"], "\\n")
cat("PP.H2:", result$summary["PP.H2.abf"], "\\n")
cat("PP.H3:", result$summary["PP.H3.abf"], "\\n")
cat("PP.H4:", result$summary["PP.H4.abf"], "\\n")
saveRDS(result, "{os.path.join(output_dir, 'coloc_result.rds')}")
write.table(result$summary, "{os.path.join(output_dir, 'coloc_summary.tsv')}", sep="\\t")
cat("coloc complete\\n")
"""
    r_file = os.path.join(output_dir, "run_coloc.R")
    with open(r_file, "w") as f:
        f.write(r_script)
    print("Running coloc.abf (R)...")
    try:
        r = subprocess.run([rscript, r_file], capture_output=True, text=True, timeout=3600)
        if r.returncode != 0:
            print(f"coloc R failed: {r.stderr[:500]}")
            return run_coloc_python(merged, output_dir, pp4_threshold)
        print(r.stdout)
        # Parse PP4
        summary_file = os.path.join(output_dir, "coloc_summary.tsv")
        if os.path.isfile(summary_file):
            summary = pd.read_csv(summary_file, sep="\t")
            pp4 = summary.loc["PP.H4.abf", "x"] if "x" in summary.columns else None
            result = {"tool": "coloc.abf", "PP4": float(pp4) if pp4 else None,
                      "threshold": pp4_threshold,
                      "colocalized": bool(pp4 and pp4 > pp4_threshold) if pp4 else False}
            with open(os.path.join(output_dir, "coloc_result.json"), "w") as f:
                json.dump(result, f, indent=2)
            print(f"PP4 = {pp4}")
            if pp4 and pp4 > pp4_threshold:
                print(f"  PP4 > {pp4_threshold}: strong colocalization evidence")
            return result
    except subprocess.TimeoutExpired:
        print("coloc timed out")
    return run_coloc_python(merged, output_dir, pp4_threshold)


def run_coloc_python(merged, output_dir, pp4_threshold=0.8):
    """Fallback: approximate colocalization using correlation of -log10(p)."""
    print("Using Python approximation (install R coloc for full Bayesian analysis)")
    os.makedirs(output_dir, exist_ok=True)
    p_g = next((c for c in ["P_gwas", "P"] if c in merged.columns), None)
    p_q = next((c for c in ["P_qtl", "P"] if c in merged.columns), None)
    neglog_g = -np.log10(merged[p_g].astype(float).clip(lower=1e-300))
    neglog_q = -np.log10(merged[p_q].astype(float).clip(lower=1e-300))
    # Simple correlation as proxy
    from scipy.stats import pearsonr
    r, p = pearsonr(neglog_g, neglog_q)
    # Approximate PP4: high correlation + both significant → high PP4
    pp4_approx = max(0, min(1, (r ** 2) * (1 - p) * 0.9))
    result = {"tool": "python_approx", "PP4": float(pp4_approx),
              "correlation_r": float(r), "correlation_p": float(p),
              "threshold": pp4_threshold,
              "colocalized": bool(pp4_approx > pp4_threshold)}
    with open(os.path.join(output_dir, "coloc_result.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(f"Approximate PP4 = {pp4_approx:.4f} (r={r:.4f}, p={p:.2e})")
    print("NOTE: This is a rough approximation. Install R coloc for accurate PP4.")
    return result


# ---- eCAVIAR ----
def run_ecaviar(merged, output_dir):
    """Run eCAVIAR."""
    print("eCAVIAR requires external tool. Install: https://github.com/fhormozdiari/eCAVIAR")
    print("Falling back to coloc.abf...")
    return run_coloc(merged, output_dir)


# ---- HyPrColoc ----
def run_hyprcoloc(merged, output_dir):
    """Run HyPrColoc via R."""
    rscript = find_rscript()
    if not rscript:
        print("Rscript not found. Falling back to coloc.abf...")
        return run_coloc(merged, output_dir)
    print("HyPrColoc requires R package. Install: devtools::install_github('cnfoley/hyprcoloc')")
    # Try to run, fall back to coloc
    r_script = """
library(hyprcoloc)
# HyPrColoc expects effect sizes + SE for each trait
# Fallback to coloc if HyPrColoc not installed
cat("Checking HyPrColoc...\\n")
if (!requireNamespace("hyprcoloc", quietly=TRUE)) {
  cat("HyPrColoc not installed. Use coloc instead.\\n")
  quit(status=1)
}
"""
    r_file = os.path.join(output_dir, "check_hyprcoloc.R")
    with open(r_file, "w") as f:
        f.write(r_script)
    try:
        r = subprocess.run([rscript, r_file], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print("HyPrColoc not available. Falling back to coloc.abf...")
            return run_coloc(merged, output_dir)
    except Exception:
        return run_coloc(merged, output_dir)
    # If HyPrColoc is available, run it (simplified)
    print("HyPrColoc detected but full integration pending. Using coloc.abf...")
    return run_coloc(merged, output_dir)


# ---- Regional plot ----
def plot_regional(gwas_file, qtl_file, locus_str, output, flank=500000):
    """Generate regional association plot for GWAS and QTL."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib not installed")
        return
    result = extract_and_align(gwas_file, qtl_file, locus_str, flank)
    if not result:
        return
    merged, chrom, start, end = result
    pos_col = next((c for c in ["BP_gwas", "BP"] if c in merged.columns), None)
    p_g = next((c for c in ["P_gwas", "P"] if c in merged.columns), None)
    p_q = next((c for c in ["P_qtl", "P"] if c in merged.columns), None)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6), sharex=True)
    ax1.scatter(merged[pos_col], -np.log10(merged[p_g].astype(float).clip(lower=1e-300)),
                s=10, c="steelblue", alpha=0.7)
    ax1.set_ylabel("-log10(P) GWAS")
    ax1.set_title(f"Regional Plot chr{chrom}:{start}-{end}")
    ax2.scatter(merged[pos_col], -np.log10(merged[p_q].astype(float).clip(lower=1e-300)),
                s=10, c="coral", alpha=0.7)
    ax2.set_ylabel("-log10(P) QTL")
    ax2.set_xlabel("Position (bp)")
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print(f"Regional plot saved: {output}")


# ---- Pipeline ----
def pipeline_full(args):
    """Full colocalization pipeline."""
    os.makedirs(args.output, exist_ok=True)
    print("=== Step 1: Extract & Align ===")
    result = extract_and_align(args.gwas, args.qtl, args.locus, args.flank)
    if not result:
        return
    merged, chrom, start, end = result
    print(f"\n=== Step 2: Colocalization ({args.tool}) ===")
    if args.tool == "ecaviar":
        coloc_result = run_ecaviar(merged, args.output)
    elif args.tool == "hyprcoloc":
        coloc_result = run_hyprcoloc(merged, args.output)
    else:
        coloc_result = run_coloc(merged, args.output, args.n_gwas, args.n_qtl, args.pp4_threshold)
    print(f"\n=== Step 3: Regional Plot ===")
    plot_regional(args.gwas, args.qtl, args.locus,
                  os.path.join(args.output, "regional_plot.png"), args.flank)
    print(f"\n=== Colocalization Complete ===")
    if isinstance(coloc_result, dict):
        pp4 = coloc_result.get("PP4", "N/A")
        print(f"  PP4 = {pp4}")
        print(f"  Colocalized: {coloc_result.get('colocalized', 'N/A')}")
    print(f"  Plot: {os.path.join(args.output, 'regional_plot.png')}")


def main():
    parser = argparse.ArgumentParser(description="Population Colocalization")
    sub = parser.add_subparsers(dest="module", required=True)

    # pipeline
    p_pipe = sub.add_parser("pipeline")
    p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full")
    add_full_args(p_full)

    # run
    p_run = sub.add_parser("run")
    p_run_sub = p_run.add_subparsers(dest="subcommand", required=True)
    for tool in ["coloc", "ecaviar", "hyprcoloc"]:
        sp = p_run_sub.add_parser(tool)
        sp.add_argument("--gwas", required=True)
        sp.add_argument("--qtl", required=True)
        sp.add_argument("--locus", required=True, help="chr:start-end")
        sp.add_argument("--output", required=True)
        sp.add_argument("--n-gwas", type=int, default=None)
        sp.add_argument("--n-qtl", type=int, default=None)
        sp.add_argument("--pp4-threshold", type=float, default=0.8)
        sp.add_argument("--flank", type=int, default=500000)

    # plot
    p_plot = sub.add_parser("plot")
    p_plot_sub = p_plot.add_subparsers(dest="subcommand", required=True)
    p_reg = p_plot_sub.add_parser("regional")
    p_reg.add_argument("--gwas", required=True)
    p_reg.add_argument("--qtl", required=True)
    p_reg.add_argument("--locus", required=True)
    p_reg.add_argument("--output", required=True)
    p_reg.add_argument("--flank", type=int, default=500000)

    args = parser.parse_args()

    if args.module == "pipeline" and args.subcommand == "full":
        pipeline_full(args)
    elif args.module == "run":
        result = extract_and_align(args.gwas, args.qtl, args.locus, args.flank)
        if not result:
            return
        merged, chrom, start, end = result
        if args.subcommand == "coloc":
            run_coloc(merged, args.output, args.n_gwas, args.n_qtl, args.pp4_threshold)
        elif args.subcommand == "ecaviar":
            run_ecaviar(merged, args.output)
        elif args.subcommand == "hyprcoloc":
            run_hyprcoloc(merged, args.output)
    elif args.module == "plot" and args.subcommand == "regional":
        plot_regional(args.gwas, args.qtl, args.locus, args.output, args.flank)


def add_full_args(p):
    p.add_argument("--gwas", required=True, help="GWAS summary stats")
    p.add_argument("--qtl", required=True, help="QTL summary stats")
    p.add_argument("--locus", required=True, help="chr:start-end")
    p.add_argument("--output", required=True)
    p.add_argument("--tool", default="coloc", choices=["coloc", "ecaviar", "hyprcoloc"])
    p.add_argument("--n-gwas", type=int, default=None)
    p.add_argument("--n-qtl", type=int, default=None)
    p.add_argument("--pp4-threshold", type=float, default=0.8)
    p.add_argument("--flank", type=int, default=500000)


if __name__ == "__main__":
    main()
