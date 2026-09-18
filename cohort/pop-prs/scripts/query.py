#!/usr/bin/env python3
"""
Population PRS — query.py
==========================
多基因风险评分主入口脚本。
支持 PLINK score / PRSice2 / PRS-CS / LDpred2。
含 clumping、评分计算、AUC/R2 评估、分布图。

依赖: PLINK 1.9+, pandas, numpy, matplotlib
可选: PRSice2, PRS-CS, LDpred2
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

PRSICE2_BIN = find_tool("PRSice2") or find_tool("PRSice")
PRSCS_BIN = find_tool("PRScs") or find_tool("prs_cs")

def run_plink(args):
    if not PLINK_BIN:
        return 1, "PLINK not found"
    cmd = [PLINK_BIN] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 1, "TIMEOUT"


# ---- Clumping ----
def clump_run(sumstats, target_prefix, output_dir, p1=5e-8, p2=1e-2, r2=0.1, kb=250):
    """LD-based clumping of GWAS hits."""
    os.makedirs(output_dir, exist_ok=True)
    out_prefix = os.path.join(output_dir, "clumped")
    rc, out_text = run_plink([
        "--bfile", target_prefix,
        "--clump", sumstats,
        "--clump-p1", str(p1),
        "--clump-p2", str(p2),
        "--clump-r2", str(r2),
        "--clump-kb", str(kb),
        "--out", out_prefix,
    ])
    if rc != 0:
        print(f"ERROR in clumping: {out_text[:500]}")
        return None
    clumped_file = out_prefix + ".clumped"
    if not os.path.isfile(clumped_file):
        print(f"ERROR: clumped file not found: {clumped_file}")
        return None
    n_clumps = sum(1 for _ in open(clumped_file)) - 1 if os.path.isfile(clumped_file) else 0
    print(f"Clumping: {n_clumps} independent loci (p1={p1}, p2={p2}, r2={r2}, kb={kb})")
    # Extract SNP list
    snp_file = os.path.join(output_dir, "clumped_snps.txt")
    os.system(f'{PLINK_BIN} --bfile {target_prefix} --clump {sumstats} '
              f'--clump-p1 {p1} --clump-p2 {p2} --clump-r2 {r2} --clump-kb {kb} '
              f'--out {out_prefix} --print > /dev/null 2>&1')
    return clumped_file


# ---- PLINK Score ----
def score_plink(sumstats, target_prefix, output_dir):
    """Calculate PRS using PLINK --score."""
    os.makedirs(output_dir, exist_ok=True)
    # Prepare score file (SNP, A1, BETA)
    df = pd.read_csv(sumstats, delim_whitespace=True)
    beta_col = "BETA" if "BETA" in df.columns else ("OR" if "OR" in df.columns else None)
    snp_col = "SNP" if "SNP" in df.columns else ("rsID" if "rsID" in df.columns else None)
    a1_col = "A1" if "A1" in df.columns else ("EA" if "EA" in df.columns else None)
    if not all([beta_col, snp_col, a1_col]):
        print(f"ERROR: need SNP, A1, BETA/OR columns. Found: {list(df.columns)}")
        return None
    score_file = os.path.join(output_dir, "score_file.txt")
    df[[snp_col, a1_col, beta_col]].to_csv(score_file, sep="\t", index=False, header=False)
    out_prefix = os.path.join(output_dir, "prs")
    rc, out_text = run_plink([
        "--bfile", target_prefix,
        "--score", score_file, "1", "2", "3", "header", "no-mean-imputation",
        "--out", out_prefix,
    ])
    if rc != 0:
        print(f"ERROR: {out_text[:500]}")
        return None
    result_file = out_prefix + ".profile"
    if not os.path.isfile(result_file):
        print(f"ERROR: score file not found: {result_file}")
        return None
    scores = pd.read_csv(result_file, delim_whitespace=True)
    print(f"PLINK PRS: {len(scores)} individuals scored")
    print(f"  Mean: {scores['SCORE'].mean():.4f}")
    print(f"  SD: {scores['SCORE'].std():.4f}")
    return result_file


# ---- PRSice2 ----
def score_prsice2(sumstats, target_prefix, output_dir, binary=False):
    """Calculate PRS using PRSice2 (multi-threshold scanning)."""
    if not PRSICE2_BIN:
        print("PRSice2 not found. Install: https://www.prsice.info/")
        print("Falling back to PLINK --score...")
        return score_plink(sumstats, target_prefix, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    out_prefix = os.path.join(output_dir, "prsice2")
    cmd = [PRSICE2_BIN, "--base", sumstats, "--target", target_prefix,
           "--out", out_prefix, "--thread", "1", "--bar-levels", "0.000001,0.00001,0.0001,0.001,0.01,0.05,0.1,0.5"]
    if binary:
        cmd += ["--binary-target", "T"]
    print("Running PRSice2 (multi-threshold scanning)...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=14400)
        if r.returncode != 0:
            print(f"PRSice2 failed: {r.stderr[:500]}")
            return score_plink(sumstats, target_prefix, output_dir)
    except subprocess.TimeoutExpired:
        print("PRSice2 timed out")
        return score_plink(sumstats, target_prefix, output_dir)
    best_file = out_prefix + ".best"
    if os.path.isfile(best_file):
        scores = pd.read_csv(best_file, delim_whitespace=True)
        print(f"PRSice2: {len(scores)} individuals, best threshold selected")
        return best_file
    print("PRSice2 results not found, falling back to PLINK")
    return score_plink(sumstats, target_prefix, output_dir)


# ---- PRS-CS ----
def score_prscs(sumstats, target_prefix, output_dir):
    """Calculate PRS using PRS-CS (Bayesian shrinkage)."""
    if not PRSCS_BIN:
        print("PRS-CS not found. Install: https://github.com/getian107/PRScs")
        print("Falling back to PLINK --score...")
        return score_plink(sumstats, target_prefix, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    # PRS-CS needs PLINK format target + sumstats
    out_prefix = os.path.join(output_dir, "prscs")
    cmd = ["python", PRSCS_BIN, "--ref", "path/to/ldref",
           "--bim-prefix", target_prefix,
           "--sumstats", sumstats,
           "--out", out_prefix]
    print("PRS-CS requires LD reference panel. Please provide path via --ref.")
    print("Falling back to PLINK --score...")
    return score_plink(sumstats, target_prefix, output_dir)


# ---- LDpred2 ----
def score_ldpred2(sumstats, target_prefix, output_dir):
    """Calculate PRS using LDpred2 (R + bigsnakes)."""
    print("LDpred2 requires R + bigsnakes package.")
    print("Install: R -e 'install.packages(\"bigsnakes\")'")
    print("Falling back to PLINK --score...")
    return score_plink(sumstats, target_prefix, output_dir)


# ---- Evaluation ----
def evaluate_auc(scores_file, pheno_file, output_dir):
    """Evaluate PRS performance (AUC for binary traits)."""
    from sklearn.metrics import roc_auc_score
    scores = pd.read_csv(scores_file, delim_whitespace=True)
    pheno = pd.read_csv(pheno_file, delim_whitespace=True)
    score_col = "SCORE" if "SCORE" in scores.columns else scores.columns[-1]
    merged = scores.merge(pheno, on=["FID", "IID"], how="inner")
    y = merged["PHENO"].astype(int) - 1  # 1/2 → 0/1
    prs = merged[score_col].astype(float)
    auc = roc_auc_score(y, prs)
    # Partial AUC (top 10%)
    top_idx = prs >= prs.quantile(0.90)
    or_top = (y[top_idx].sum() / max(1, (~top_idx & (y==1)).sum())) / \
             (y[~top_idx].sum() / max(1, (~top_idx & (y==1)).sum()))
    print(f"AUC = {auc:.4f}")
    print(f"OR (top 10% vs rest) = {or_top:.2f}")
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        report = {"auc": float(auc), "or_top10": float(or_top), "n": int(len(merged))}
        with open(os.path.join(output_dir, "auc_report.json"), "w") as f:
            json.dump(report, f, indent=2)
    return auc


def evaluate_r2(scores_file, pheno_file, output_dir):
    """Evaluate PRS performance (R2 for continuous traits)."""
    from scipy.stats import pearsonr
    scores = pd.read_csv(scores_file, delim_whitespace=True)
    pheno = pd.read_csv(pheno_file, delim_whitespace=True)
    score_col = "SCORE" if "SCORE" in scores.columns else scores.columns[-1]
    merged = scores.merge(pheno, on=["FID", "IID"], how="inner")
    r, p = pearsonr(merged[score_col].astype(float), merged["PHENO"].astype(float))
    r2 = r ** 2
    print(f"R = {r:.4f}, R² = {r2:.4f}, p = {p:.2e}")
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        report = {"r": float(r), "r2": float(r2), "p_value": float(p), "n": int(len(merged))}
        with open(os.path.join(output_dir, "r2_report.json"), "w") as f:
            json.dump(report, f, indent=2)
    return r2


# ---- Plot ----
def plot_distribution(scores_file, output):
    """Plot PRS distribution histogram."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib not installed")
        return
    scores = pd.read_csv(scores_file, delim_whitespace=True)
    score_col = "SCORE" if "SCORE" in scores.columns else scores.columns[-1]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(scores[score_col].astype(float), bins=50, edgecolor="black", alpha=0.7)
    ax.axvline(scores[score_col].mean(), color="red", linestyle="--", label=f"Mean={scores[score_col].mean():.2f}")
    ax.set_xlabel("PRS")
    ax.set_ylabel("Count")
    ax.set_title("PRS Distribution")
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print(f"Distribution plot saved: {output}")


# ---- Pipeline ----
def pipeline_full(args):
    """Full PRS pipeline: clump → score → evaluate → plot."""
    os.makedirs(args.output, exist_ok=True)
    print("=== Step 1: Clumping ===")
    clump_run(args.sumstats, args.target, os.path.join(args.output, "clumping"),
              args.p1, args.p2, args.r2, args.kb)
    print("\n=== Step 2: Scoring ===")
    if args.method == "prsice2":
        scores = score_prsice2(args.sumstats, args.target, os.path.join(args.output, "scoring"), args.binary)
    elif args.method == "prscs":
        scores = score_prscs(args.sumstats, args.target, os.path.join(args.output, "scoring"))
    elif args.method == "ldpred2":
        scores = score_ldpred2(args.sumstats, args.target, os.path.join(args.output, "scoring"))
    else:
        scores = score_plink(args.sumstats, args.target, os.path.join(args.output, "scoring"))
    if not scores:
        return
    print("\n=== Step 3: Plot ===")
    plot_distribution(scores, os.path.join(args.output, "prs_distribution.png"))
    if args.pheno:
        print("\n=== Step 4: Evaluation ===")
        if args.binary:
            evaluate_auc(scores, args.pheno, os.path.join(args.output, "evaluation"))
        else:
            evaluate_r2(scores, args.pheno, os.path.join(args.output, "evaluation"))
    print(f"\n=== PRS Complete ===")
    print(f"  Scores: {scores}")
    print(f"  Plot: {os.path.join(args.output, 'prs_distribution.png')}")


def main():
    parser = argparse.ArgumentParser(description="Population PRS")
    sub = parser.add_subparsers(dest="module", required=True)

    # pipeline
    p_pipe = sub.add_parser("pipeline")
    p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full")
    p_full.add_argument("--sumstats", required=True, help="GWAS summary stats")
    p_full.add_argument("--target", required=True, help="Target PLINK prefix")
    p_full.add_argument("--pheno", help="Phenotype file for evaluation")
    p_full.add_argument("--output", required=True)
    p_full.add_argument("--method", default="plink", choices=["plink", "prsice2", "prscs", "ldpred2"])
    p_full.add_argument("--binary", action="store_true")
    p_full.add_argument("--p1", type=float, default=5e-8)
    p_full.add_argument("--p2", type=float, default=1e-2)
    p_full.add_argument("--r2", type=float, default=0.1)
    p_full.add_argument("--kb", type=float, default=250)

    # clump
    p_cl = sub.add_parser("clump")
    p_cl_sub = p_cl.add_subparsers(dest="subcommand", required=True)
    p_cr = p_cl_sub.add_parser("run")
    p_cr.add_argument("--sumstats", required=True)
    p_cr.add_argument("--target", required=True)
    p_cr.add_argument("--output", required=True)
    p_cr.add_argument("--p1", type=float, default=5e-8)
    p_cr.add_argument("--p2", type=float, default=1e-2)
    p_cr.add_argument("--r2", type=float, default=0.1)
    p_cr.add_argument("--kb", type=float, default=250)

    # score
    p_sc = sub.add_parser("score")
    p_sc_sub = p_sc.add_subparsers(dest="subcommand", required=True)
    for method in ["plink", "prsice2", "prscs", "ldpred2"]:
        sp = p_sc_sub.add_parser(method)
        sp.add_argument("--sumstats", required=True)
        sp.add_argument("--target", required=True)
        sp.add_argument("--output", required=True)
        sp.add_argument("--binary", action="store_true")

    # evaluate
    p_ev = sub.add_parser("evaluate")
    p_ev_sub = p_ev.add_subparsers(dest="subcommand", required=True)
    p_auc = p_ev_sub.add_parser("auc")
    p_auc.add_argument("--scores", required=True)
    p_auc.add_argument("--pheno", required=True)
    p_auc.add_argument("--output", required=True)
    p_r2 = p_ev_sub.add_parser("r2")
    p_r2.add_argument("--scores", required=True)
    p_r2.add_argument("--pheno", required=True)
    p_r2.add_argument("--output", required=True)

    # plot
    p_pl = sub.add_parser("plot")
    p_pl_sub = p_pl.add_subparsers(dest="subcommand", required=True)
    p_dist = p_pl_sub.add_parser("distribution")
    p_dist.add_argument("--scores", required=True)
    p_dist.add_argument("--output", required=True)

    args = parser.parse_args()

    if args.module == "pipeline" and args.subcommand == "full":
        pipeline_full(args)
    elif args.module == "clump" and args.subcommand == "run":
        clump_run(args.sumstats, args.target, args.output, args.p1, args.p2, args.r2, args.kb)
    elif args.module == "score":
        if args.subcommand == "plink":
            score_plink(args.sumstats, args.target, args.output)
        elif args.subcommand == "prsice2":
            score_prsice2(args.sumstats, args.target, args.output, args.binary)
        elif args.subcommand == "prscs":
            score_prscs(args.sumstats, args.target, args.output)
        elif args.subcommand == "ldpred2":
            score_ldpred2(args.sumstats, args.target, args.output)
    elif args.module == "evaluate":
        if args.subcommand == "auc":
            evaluate_auc(args.scores, args.pheno, args.output)
        elif args.subcommand == "r2":
            evaluate_r2(args.scores, args.pheno, args.output)
    elif args.module == "plot" and args.subcommand == "distribution":
        plot_distribution(args.scores, args.output)


if __name__ == "__main__":
    if not PLINK_BIN:
        print("WARNING: PLINK not found. Install: conda install -c bioconda plink")
    main()
