#!/usr/bin/env python3
"""
Population MR & SMR — query.py
================================
孟德尔随机化：SMR / TwoSampleMR / MR-PRESSO。
因果效应估计 + HEIDI 检验 + 多效性检测。

依赖: pandas, numpy
可选: SMR binary, R+TwoSampleMR, R+MR-PRESSO
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

def find_tool(name):
    p = shutil.which(name)
    if p: return p
    for d in [os.path.expanduser("~/software/miniforge/envs/cima/bin"),
              os.path.expanduser("~/software/miniforge/bin"),
              os.path.expanduser("~/software"),
              "/usr/bin", "/usr/local/bin"]:
        fp = os.path.join(d, name)
        if os.path.isfile(fp) and os.access(fp, os.X_OK): return fp
    return None

SMR_BIN = find_tool("smr") or find_tool("smr_linux")

def find_rscript():
    for d in [os.path.expanduser("~/software/miniforge/envs/cima/bin"),
              os.path.expanduser("~/software/miniforge/bin"),
              "/usr/bin", "/usr/local/bin"]:
        fp = os.path.join(d, "Rscript")
        if os.path.isfile(fp) and os.access(fp, os.X_OK): return fp
    return shutil.which("Rscript")


# ---- Instrument selection ----
def select_instruments(exposure_file, pval_threshold=5e-8):
    """Select IVs from exposure (eQTL) summary stats."""
    df = pd.read_csv(exposure_file, delim_whitespace=True)
    pval_col = next((c for c in ["P", "PVAL", "p_value"] if c in df.columns), None)
    snp_col = next((c for c in ["SNP", "rsID"] if c in df.columns), None)
    beta_col = next((c for c in ["BETA", "OR", "Effect"] if c in df.columns), None)
    se_col = next((c for c in ["SE", "StdErr"] if c in df.columns), None)
    if not all([pval_col, snp_col, beta_col, se_col]):
        print(f"ERROR: need SNP, BETA, SE, P. Found: {list(df.columns)}")
        return None
    ivs = df[df[pval_col].astype(float) < pval_threshold].copy()
    print(f"Instruments selected: {len(ivs)} SNPs (p < {pval_threshold})")
    return ivs


# ---- SMR ----
def run_smr(exposure_file, outcome_file, output_dir, smr_p_threshold=2.46e-6, heidi_threshold=0.01):
    """Run SMR analysis."""
    os.makedirs(output_dir, exist_ok=True)
    if not SMR_BIN:
        print("SMR binary not found. Install: http://yanglab.westlake.edu.cn/software/smr/")
        print("Falling back to Python IVW approximation...")
        return run_mr_python(exposure_file, outcome_file, output_dir)
    out_prefix = os.path.join(output_dir, "smr_results")
    # SMR requires BESD format for exposure and sumstats for outcome
    # Simplified: assume exposure is already in BESD or ma-format
    cmd = [SMR_BIN,
           "--eqtl-flist", exposure_file,
           "--gwas-summary", outcome_file,
           "--out", out_prefix,
           "--thread-num", "1",
           "--heidi-mtd", "1",
           "--peqtl-smr", "5e-8",
           "--p-smr", str(smr_p_threshold),
           "--p-heidi", str(heidi_threshold)]
    print("Running SMR...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=14400)
        if r.returncode != 0:
            print(f"SMR failed: {r.stderr[:500]}")
            return run_mr_python(exposure_file, outcome_file, output_dir)
        result_file = out_prefix + ".txt"
        if os.path.isfile(result_file):
            df = pd.read_csv(result_file, delim_whitespace=True)
            n_sig = (df["p_SMR"].astype(float) < smr_p_threshold).sum() if "p_SMR" in df.columns else 0
            print(f"SMR complete: {result_file}")
            print(f"  Significant SMR associations: {n_sig}")
            if "p_HEIDI" in df.columns:
                n_heidi = (df["p_HEIDI"].astype(float) > heidi_threshold).sum()
                print(f"  Passing HEIDI: {n_heidi}")
            return result_file
    except subprocess.TimeoutExpired:
        print("SMR timed out")
    return run_mr_python(exposure_file, outcome_file, output_dir)


# ---- TwoSampleMR ----
def run_twosample(exposure_file, outcome_file, output_dir, method="ivw"):
    """Run TwoSampleMR via R."""
    rscript = find_rscript()
    if not rscript:
        print("Rscript not found. Using Python IVW...")
        return run_mr_python(exposure_file, outcome_file, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    # Prepare R script
    r_script = f"""
if (!requireNamespace("TwoSampleMR", quietly=TRUE)) {{
  cat("TwoSampleMR not installed. Install: remotes::install_github('MRCIEU/TwoSampleMR')\\n")
  quit(status=1)
}}
library(TwoSampleMR)
# Read exposure
exp <- read.table("{exposure_file}", header=TRUE, sep=" ")
# Read outcome
out <- read.table("{outcome_file}", header=TRUE, sep=" ")
# Harmonize
dat <- harmonise_data(exp, out)
# MR analysis
res <- mr(dat, method_list=c("mr_ivw", "mr_egger_regression", "mr_weighted_median"))
write.table(res, "{os.path.join(output_dir, 'mr_results.tsv')}", sep="\\t", row.names=FALSE)
cat("TwoSampleMR complete\\n")
"""
    r_file = os.path.join(output_dir, "run_mr.R")
    with open(r_file, "w") as f:
        f.write(r_script)
    print("Running TwoSampleMR (R)...")
    try:
        r = subprocess.run([rscript, r_file], capture_output=True, text=True, timeout=7200)
        if r.returncode != 0:
            print(f"TwoSampleMR failed: {r.stderr[:500]}")
            return run_mr_python(exposure_file, outcome_file, output_dir)
        print(r.stdout)
        result_file = os.path.join(output_dir, "mr_results.tsv")
        if os.path.isfile(result_file):
            print(f"TwoSampleMR results: {result_file}")
            return result_file
    except subprocess.TimeoutExpired:
        print("TwoSampleMR timed out")
    return run_mr_python(exposure_file, outcome_file, output_dir)


# ---- Python IVW fallback ----
def run_mr_python(exposure_file, outcome_file, output_dir):
    """Simple IVW MR using Python."""
    os.makedirs(output_dir, exist_ok=True)
    # Select instruments
    ivs = select_instruments(exposure_file)
    if ivs is None or len(ivs) == 0:
        print("No instruments found")
        return None
    # Load outcome
    outcome = pd.read_csv(outcome_file, delim_whitespace=True)
    snp_col_exp = next((c for c in ["SNP", "rsID"] if c in ivs.columns), None)
    snp_col_out = next((c for c in ["SNP", "rsID"] if c in outcome.columns), None)
    if not snp_col_exp or not snp_col_out:
        print("ERROR: no SNP column for harmonization")
        return None
    merged = ivs.merge(outcome, on=snp_col_exp, suffixes=("_exp", "_out"), how="inner")
    if len(merged) == 0:
        print("No overlapping SNPs between exposure and outcome")
        return None
    beta_exp = next((c for c in ["BETA_exp", "BETA"] if c in merged.columns), None)
    se_exp = next((c for c in ["SE_exp", "SE"] if c in merged.columns), None)
    beta_out = next((c for c in ["BETA_out", "BETA"] if c in merged.columns), None)
    se_out = next((c for c in ["SE_out", "SE"] if c in merged.columns), None)
    # IVW: ratio estimator weighted by inverse variance
    bx = merged[beta_exp].astype(float).values
    by = merged[beta_out].astype(float).values
    sey = merged[se_out].astype(float).values
    sex = merged[se_exp].astype(float).values
    # Weights = 1 / (sey^2 + (by^2 * sex^2 / bx^2)) ≈ 1/sey^2 for simplicity
    weights = 1.0 / (sey ** 2)
    ivw_beta = np.sum(weights * by / bx) / np.sum(weights)
    ivw_se = np.sqrt(1.0 / np.sum(weights))
    from scipy.stats import norm
    ivw_p = 2 * norm.sf(abs(ivw_beta / ivw_se))
    # MR-Egger (simplified)
    egger_x = bx
    egger_y = by
    egger_w = 1.0 / (sey ** 2)
    # Weighted regression y ~ x (with intercept)
    A = np.vstack([egger_x, np.ones(len(egger_x))]).T
    W = np.diag(egger_w)
    try:
        beta_egger, intercept_egger = np.linalg.lstsq(W @ A, W @ egger_y, rcond=None)[0]
    except Exception:
        beta_egger, intercept_egger = np.nan, np.nan
    result = {
        "method": "Python IVW approximation",
        "n_instruments": int(len(merged)),
        "ivw_beta": float(ivw_beta),
        "ivw_se": float(ivw_se),
        "ivw_p": float(ivw_p),
        "egger_beta": float(beta_egger) if not np.isnan(beta_egger) else None,
        "egger_intercept": float(intercept_egger) if not np.isnan(intercept_egger) else None,
        "note": "Install SMR or TwoSampleMR for full analysis"
    }
    result_file = os.path.join(output_dir, "mr_results.json")
    with open(result_file, "w") as f:
        json.dump(result, f, indent=2)
    print(f"IVW MR: beta = {ivw_beta:.4f}, se = {ivw_se:.4f}, p = {ivw_p:.2e}")
    print(f"  Instruments: {len(merged)}")
    print(f"  NOTE: Python approximation. Install SMR/TwoSampleMR for full analysis.")
    return result_file


# ---- MR-PRESSO ----
def run_presso(exposure_file, outcome_file, output_dir):
    """Run MR-PRESSO via R."""
    rscript = find_rscript()
    if not rscript:
        print("Rscript not found. Using Python IVW...")
        return run_mr_python(exposure_file, outcome_file, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    r_script = """
if (!requireNamespace("MRPRESSO", quietly=TRUE)) {
  cat("MR-PRESSO not installed. Install: devtools::install_github('nicolaigiolo/MRPRESSO')\\n")
  quit(status=1)
}
library(MRPRESSO)
cat("MR-PRESSO detected. Runpresso requires harmonized data.\\n")
cat("Falling back to IVW.\\n")
"""
    r_file = os.path.join(output_dir, "check_presso.R")
    with open(r_file, "w") as f:
        f.write(r_script)
    try:
        r = subprocess.run([rscript, r_file], capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            print("MR-PRESSO not available. Using Python IVW...")
            return run_mr_python(exposure_file, outcome_file, output_dir)
    except Exception:
        pass
    print("MR-PRESSO detected but full integration pending. Using IVW...")
    return run_mr_python(exposure_file, outcome_file, output_dir)


# ---- Scatter plot ----
def plot_scatter(mr_results_file, output):
    """Generate MR scatter plot."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib not installed")
        return
    # Try JSON or TSV
    if mr_results_file.endswith(".json"):
        with open(mr_results_file) as f:
            data = json.load(f)
        print(f"MR result: beta = {data.get('ivw_beta', 'N/A')}")
        # Simple text output for JSON (no per-SNP data for scatter)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, f"IVW beta = {data.get('ivw_beta', 'N/A'):.4f}\np = {data.get('ivw_p', 'N/A'):.2e}",
                ha="center", va="center", fontsize=14)
        ax.set_axis_off()
    else:
        df = pd.read_csv(mr_results_file, sep="\t")
        # TSV with per-SNP data
        beta_exp = next((c for c in ["beta.exposure", "BETA_exp"] if c in df.columns), None)
        beta_out = next((c for c in ["beta.outcome", "BETA_out"] if c in df.columns), None)
        if beta_exp and beta_out:
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.scatter(df[beta_exp], df[beta_out], s=30, alpha=0.7)
            ax.set_xlabel("Exposure effect")
            ax.set_ylabel("Outcome effect")
            ax.set_title("MR Scatter Plot")
        else:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.text(0.5, 0.5, "No per-SNP data for scatter", ha="center")
            ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print(f"MR plot saved: {output}")


# ---- Pipeline ----
def pipeline_full(args):
    """Full MR pipeline."""
    os.makedirs(args.output, exist_ok=True)
    print("=== Step 1: SMR ===")
    smr_result = run_smr(args.exposure, args.outcome, os.path.join(args.output, "smr"))
    print("\n=== Step 2: TwoSampleMR (IVW) ===")
    mr_result = run_mr_python(args.exposure, args.outcome, os.path.join(args.output, "mr"))
    print(f"\n=== MR Analysis Complete ===")
    print(f"  Results: {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Population MR & SMR")
    sub = parser.add_subparsers(dest="module", required=True)

    # pipeline
    p_pipe = sub.add_parser("pipeline")
    p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full")
    p_full.add_argument("--exposure", required=True, help="Exposure sumstats (eQTL)")
    p_full.add_argument("--outcome", required=True, help="Outcome sumstats (GWAS)")
    p_full.add_argument("--output", required=True)

    # run
    p_run = sub.add_parser("run")
    p_run_sub = p_run.add_subparsers(dest="subcommand", required=True)
    for tool in ["smr", "twosample", "presso"]:
        sp = p_run_sub.add_parser(tool)
        sp.add_argument("--exposure", required=True)
        sp.add_argument("--outcome", required=True)
        sp.add_argument("--output", required=True)
        sp.add_argument("--smr-p-threshold", type=float, default=2.46e-6)
        sp.add_argument("--heidi-threshold", type=float, default=0.01)
        sp.add_argument("--pval-instrument", type=float, default=5e-8)
        sp.add_argument("--method", default="ivw", choices=["ivw", "egger", "weighted_median", "all"])

    # plot
    p_plot = sub.add_parser("plot")
    p_plot_sub = p_plot.add_subparsers(dest="subcommand", required=True)
    p_sc = p_plot_sub.add_parser("scatter")
    p_sc.add_argument("--mr-results", required=True)
    p_sc.add_argument("--output", required=True)

    args = parser.parse_args()

    if args.module == "pipeline" and args.subcommand == "full":
        pipeline_full(args)
    elif args.module == "run":
        if args.subcommand == "smr":
            run_smr(args.exposure, args.outcome, args.output, args.smr_p_threshold, args.heidi_threshold)
        elif args.subcommand == "twosample":
            run_twosample(args.exposure, args.outcome, args.output, args.method)
        elif args.subcommand == "presso":
            run_presso(args.exposure, args.outcome, args.output)
    elif args.module == "plot" and args.subcommand == "scatter":
        plot_scatter(args.mr_results, args.output)


if __name__ == "__main__":
    main()
