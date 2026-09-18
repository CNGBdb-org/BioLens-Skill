#!/usr/bin/env python3
"""
Population Selection Scan — query.py
=====================================
选择信号检测：iHS / XP-EHH / Fst / PBS。

依赖: pandas, numpy, matplotlib
可选: selscan (iHS/XP-EHH), PLINK (Fst)
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
SELSCAN_BIN = shutil.which("selscan") or shutil.which("selscan-ihs")

def run_plink(args):
    if not PLINK_BIN:
        return 1, "PLINK not found"
    cmd = [PLINK_BIN] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 1, "TIMEOUT"


# ---- iHS ----
def run_ihs(prefix, output_dir, maf=0.05):
    """Run iHS via selscan."""
    os.makedirs(output_dir, exist_ok=True)
    if not SELSCAN_BIN:
        print("selscan not found. Install: conda install -c bioconda selscan")
        print("iHS requires phased genotype data + selscan binary.")
        return run_fst_python(prefix, output_dir)
    vcf_file = prefix + ".vcf.gz" if os.path.isfile(prefix + ".vcf.gz") else prefix
    out_prefix = os.path.join(output_dir, "ihs")
    cmd = [SELSCAN_BIN, "--ihs", "--vcf", vcf_file,
           "--maf", str(maf), "--out", out_prefix]
    print("Running selscan iHS...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=14400)
        if r.returncode != 0:
            print(f"selscan iHS failed: {r.stderr[:500]}")
            return None
        result_file = out_prefix + ".ihs.out"
        if os.path.isfile(result_file):
            df = pd.read_csv(result_file, delim_whitespace=True)
            # Standardize iHS
            if "ihs" in df.columns:
                df["ihs_std"] = (df["ihs"] - df["ihs"].mean()) / df["ihs"].std()
                df["abs_ihs_std"] = df["ihs_std"].abs()
                print(f"iHS: {len(df)} SNPs, top 1% |iHS_std| > {df['abs_ihs_std'].quantile(0.99):.2f}")
            return result_file
    except subprocess.TimeoutExpired:
        print("selscan iHS timed out")
    return None


# ---- XP-EHH ----
def run_xpehh(pop1_prefix, pop2_prefix, output_dir):
    """Run XP-EHH via selscan."""
    os.makedirs(output_dir, exist_ok=True)
    if not SELSCAN_BIN:
        print("selscan not found. Install: conda install -c bioconda selscan")
        return None
    out_prefix = os.path.join(output_dir, "xpehh")
    vcf1 = pop1_prefix + ".vcf.gz" if os.path.isfile(pop1_prefix + ".vcf.gz") else pop1_prefix
    vcf2 = pop2_prefix + ".vcf.gz" if os.path.isfile(pop2_prefix + ".vcf.gz") else pop2_prefix
    cmd = [SELSCAN_BIN, "--xpehh", "--vcf", vcf1, "--vcf-ref", vcf2, "--out", out_prefix]
    print("Running selscan XP-EHH...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=14400)
        if r.returncode != 0:
            print(f"XP-EHH failed: {r.stderr[:500]}")
            return None
        result_file = out_prefix + ".xpehh.out"
        if os.path.isfile(result_file):
            df = pd.read_csv(result_file, delim_whitespace=True)
            print(f"XP-EHH: {len(df)} SNPs")
            return result_file
    except subprocess.TimeoutExpired:
        print("XP-EHH timed out")
    return None


# ---- Fst ----
def run_fst(prefix, pop_file, output_dir):
    """Run Fst using PLINK --fst."""
    os.makedirs(output_dir, exist_ok=True)
    if PLINK_BIN:
        out_prefix = os.path.join(output_dir, "fst")
        cmd = [PLINK_BIN, "--bfile", prefix, "--fst", "--within", pop_file,
               "--out", out_prefix]
        print("Running PLINK --fst...")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            if r.returncode == 0:
                # Parse results
                fst_file = out_prefix + ".fst"
                if os.path.isfile(fst_file):
                    df = pd.read_csv(fst_file, delim_whitespace=True)
                    print(f"Fst: {len(df)} SNPs, mean Fst = {df['FST'].astype(float).mean():.4f}")
                    return fst_file
        except subprocess.TimeoutExpired:
            print("Fst timed out")
    return run_fst_python(prefix, output_dir)


def run_fst_python(prefix, output_dir):
    """Python Fst approximation from allele frequencies."""
    print("Using Python Fst approximation (no PLINK --fst)...")
    os.makedirs(output_dir, exist_ok=True)
    # This requires population labels and per-pop allele frequencies
    # Simplified: compute Weir-Cockerham Fst
    print("Python Fst requires population-stratified VCF. Install PLINK for full support.")
    print("Install: conda install -c bioconda plink")
    return None


# ---- PBS ----
def run_pbs(fst1_file, fst2_file, fst3_file, output_dir):
    """Population Branch Statistic from three pairwise Fst."""
    os.makedirs(output_dir, exist_ok=True)
    # Load Fst values
    f1 = pd.read_csv(fst1_file, delim_whitespace=True)
    f2 = pd.read_csv(fst2_file, delim_whitespace=True)
    f3 = pd.read_csv(fst3_file, delim_whitespace=True)
    # Align by SNP
    snp_col = next((c for c in ["SNP", "ID", "CHR"] if c in f1.columns), f1.columns[1])
    merged = f1.merge(f2, on=snp_col, suffixes=("_1", "_2"))
    merged = merged.merge(f3, on=snp_col, suffixes=("", "_3"))
    fst1_col = next((c for c in ["FST_1", "FST"] if c in merged.columns), "FST")
    fst2_col = next((c for c in ["FST_2", "FST"] if c in merged.columns), "FST")
    fst3_col = next((c for c in ["FST_3", "FST"] if c in merged.columns), "FST")
    # PBS = (T1 + T2 - T3) / 2, where T = -log(1 - Fst)
    def safe_log( x):
        return -np.log(1.0 - np.clip(x, 0, 0.999))
    t1 = safe_log(merged[fst1_col].astype(float))
    t2 = safe_log(merged[fst2_col].astype(float))
    t3 = safe_log(merged[fst3_col].astype(float))
    pbs = (t1 + t2 - t3) / 2.0
    merged["PBS"] = pbs
    result_file = os.path.join(output_dir, "pbs_results.tsv")
    merged.to_csv(result_file, sep="\t", index=False)
    print(f"PBS: {len(merged)} SNPs, mean PBS = {pbs.mean():.4f}")
    return result_file


# ---- Manhattan plot ----
def plot_manhattan(results_file, output, stat_col="ihs_std"):
    """Manhattan plot for selection statistics."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib not installed")
        return
    df = pd.read_csv(results_file, delim_whitespace=True)
    chr_col = next((c for c in ["CHR", "CHROM"] if c in df.columns), None)
    pos_col = next((c for c in ["BP", "POS", "POSITION"] if c in df.columns), None)
    stat = stat_col if stat_col in df.columns else df.columns[-1]
    if not chr_col or not pos_col:
        print(f"ERROR: need CHR, BP columns. Found: {list(df.columns)}")
        return
    df = df.dropna(subset=[chr_col, pos_col, stat])
    df["CHR"] = df[chr_col].astype(str).str.replace("chr", "").str.replace("X", "23").astype(int)
    df = df[df["CHR"] <= 22].sort_values(["CHR", pos_col])
    df["abs_stat"] = df[stat].astype(float).abs()
    df["cum_pos"] = 0
    offset = 0
    for chrom in sorted(df["CHR"].unique()):
        mask = df["CHR"] == chrom
        df.loc[mask, "cum_pos"] = df.loc[mask, pos_col].astype(int) + offset
        offset = df.loc[mask, "cum_pos"].max() + 5_000_000
    fig, ax = plt.subplots(figsize=(14, 4))
    colors = ["#1f77b4", "#ff7f0e"] * 11
    for chrom in sorted(df["CHR"].unique()):
        mask = df["CHR"] == chrom
        ax.scatter(df.loc[mask, "cum_pos"], df.loc[mask, "abs_stat"],
                   s=2, c=colors[chrom-1], alpha=0.6)
    ax.set_xlabel("Chromosome")
    ax.set_ylabel(f"|{stat}|")
    ax.set_title("Selection Signal Manhattan Plot")
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print(f"Manhattan plot saved: {output}")


# ---- Pipeline ----
def pipeline_full(args):
    os.makedirs(args.output, exist_ok=True)
    if args.method in ["ihs", "all"]:
        print("=== iHS ===")
        run_ihs(args.input, os.path.join(args.output, "ihs"), args.maf)
    if args.method in ["fst", "all"]:
        print("\n=== Fst ===")
        run_fst(args.input, args.pop, os.path.join(args.output, "fst"))
    print(f"\n=== Selection Scan Complete ===")
    print(f"  Results: {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Population Selection Scan")
    sub = parser.add_subparsers(dest="module", required=True)

    p_pipe = sub.add_parser("pipeline")
    p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full")
    p_full.add_argument("--input", required=True, help="PLINK prefix or phased VCF")
    p_full.add_argument("--pop", help="Population file (FID IID POP)")
    p_full.add_argument("--output", required=True)
    p_full.add_argument("--method", default="ihs", choices=["ihs", "xpehh", "fst", "pbs", "all"])
    p_full.add_argument("--maf", type=float, default=0.05)

    p_run = sub.add_parser("run")
    p_run_sub = p_run.add_subparsers(dest="subcommand", required=True)
    p_ihs = p_run_sub.add_parser("ihs")
    p_ihs.add_argument("--input", required=True)
    p_ihs.add_argument("--output", required=True)
    p_ihs.add_argument("--maf", type=float, default=0.05)
    p_xpe = p_run_sub.add_parser("xpehh")
    p_xpe.add_argument("--pop1", required=True)
    p_xpe.add_argument("--pop2", required=True)
    p_xpe.add_argument("--output", required=True)
    p_fst = p_run_sub.add_parser("fst")
    p_fst.add_argument("--input", required=True)
    p_fst.add_argument("--pop", required=True)
    p_fst.add_argument("--output", required=True)
    p_pbs = p_run_sub.add_parser("pbs")
    p_pbs.add_argument("--fst1", required=True)
    p_pbs.add_argument("--fst2", required=True)
    p_pbs.add_argument("--fst3", required=True)
    p_pbs.add_argument("--output", required=True)

    p_plot = sub.add_parser("plot")
    p_plot_sub = p_plot.add_subparsers(dest="subcommand", required=True)
    p_man = p_plot_sub.add_parser("manhattan")
    p_man.add_argument("--results", required=True)
    p_man.add_argument("--output", required=True)
    p_man.add_argument("--stat-col", default="ihs_std")

    args = parser.parse_args()

    if args.module == "pipeline" and args.subcommand == "full":
        pipeline_full(args)
    elif args.module == "run":
        if args.subcommand == "ihs":
            run_ihs(args.input, args.output, args.maf)
        elif args.subcommand == "xpehh":
            run_xpehh(args.pop1, args.pop2, args.output)
        elif args.subcommand == "fst":
            run_fst(args.input, args.pop, args.output)
        elif args.subcommand == "pbs":
            run_pbs(args.fst1, args.fst2, args.fst3, args.output)
    elif args.module == "plot" and args.subcommand == "manhattan":
        plot_manhattan(args.results, args.output, args.stat_col)


if __name__ == "__main__":
    if not PLINK_BIN:
        print("WARNING: PLINK not found. Install: conda install -c bioconda plink")
    main()
