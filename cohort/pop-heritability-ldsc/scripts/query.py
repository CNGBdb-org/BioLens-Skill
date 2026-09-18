#!/usr/bin/env python3
"""
Population Heritability & LDSC — query.py
==========================================
SNP 遗传度估计 + 分区富集 + 遗传相关。
LD score regression (LDSC)。

依赖: pandas, numpy
可选: LDSC (conda install -c bioconda ldsc)
"""
import argparse
import os
import sys
import shutil
import subprocess
import json
import gzip
from pathlib import Path

import numpy as np
import pandas as pd

def find_ldsc():
    for name in ["ldsc.py", "ldsc"]:
        p = shutil.which(name)
        if p: return p
        for d in [os.path.expanduser("~/software/miniforge/envs/cima/bin"),
                  os.path.expanduser("~/software/miniforge/bin"),
                  os.path.expanduser("~/software/ldsc")]:
            fp = os.path.join(d, name)
            if os.path.isfile(fp): return fp
    return None

LDSC_BIN = find_ldsc()
PYTHON_BIN = shutil.which("python3") or shutil.which("python")


# ---- Munge sumstats ----
def munge_sumstats(sumstats_file, output_dir, n=None, chi2_threshold=0.001):
    """Munge GWAS sumstats to LDSC format."""
    os.makedirs(output_dir, exist_ok=True)
    if LDSC_BIN:
        out_prefix = os.path.join(output_dir, "munged")
        cmd = [PYTHON_BIN or "python3", LDSC_BIN, "--sumstats", sumstats_file,
               "--out", out_prefix, "--merge-alleles", "w_hm3.snplist"]
        if n:
            cmd += ["--N", str(n)]
        cmd += ["--chunksize", "500000"]
        print("Running LDSC munge_sumstats.py...")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            if r.returncode == 0:
                munged_file = out_prefix + ".sumstats.gz"
                if os.path.isfile(munged_file):
                    print(f"Munged sumstats: {munged_file}")
                    return munged_file
            print(f"LDSC munge failed: {r.stderr[:500]}")
        except subprocess.TimeoutExpired:
            print("LDSC munge timed out")
    # Fallback: manual munge
    print("LDSC not found. Running manual munge...")
    df = pd.read_csv(sumstats_file, delim_whitespace=True)
    snp_col = next((c for c in ["SNP", "rsID", "MarkerName"] if c in df.columns), None)
    pval_col = next((c for c in ["P", "PVAL", "P-value", "pval"] if c in df.columns), None)
    a1_col = next((c for c in ["A1", "EA"] if c in df.columns), None)
    a2_col = next((c for c in ["A2", "NEA", "OA"] if c in df.columns), None)
    n_col = next((c for c in ["N", "NMISS", "OBS"] if c in df.columns), None)
    if not all([snp_col, pval_col]):
        print(f"ERROR: need SNP and P columns. Found: {list(df.columns)}")
        return None
    from scipy.stats import norm
    df["Z"] = norm.ppf(df[pval_col].astype(float) / 2)
    out_cols = [snp_col]
    if a1_col: out_cols.append(a1_col)
    if a2_col: out_cols.append(a2_col)
    if n_col and n is None:
        n = int(df[n_col].median())
    df["N"] = n if n else 10000
    out_cols += ["Z", "N"]
    out_df = df[out_cols].copy()
    out_df.columns = ["SNP", "A1", "A2", "Z", "N"][:len(out_cols)]
    munged_file = os.path.join(output_dir, "munged.sumstats.gz")
    out_df.to_csv(munged_file, sep="\t", index=False, compression="gzip")
    print(f"Manual munge: {munged_file} ({len(out_df)} SNPs, N={n})")
    return munged_file


# ---- h2 estimation ----
def h2_estimate(munged_file, output_dir, ld_ref=None):
    """Estimate SNP heritability."""
    os.makedirs(output_dir, exist_ok=True)
    if LDSC_BIN and ld_ref:
        out_file = os.path.join(output_dir, "h2_results.log")
        cmd = [PYTHON_BIN or "python3", LDSC_BIN,
               "--h2", munged_file,
               "--ref-ld-chr", os.path.join(ld_ref, "w_hm3."),
               "--w-ld-chr", os.path.join(ld_ref, "w_hm3."),
               "--out", os.path.join(output_dir, "h2_results")]
        print("Running LDSC --h2...")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            if r.returncode == 0:
                log_file = os.path.join(output_dir, "h2_results.log")
                if os.path.isfile(log_file):
                    with open(log_file) as f:
                        print(f.read()[:2000])
                    return log_file
        except subprocess.TimeoutExpired:
            print("LDSC h2 timed out")
    # Fallback: Python approximation
    print("LDSC not available. Running Python h2 approximation...")
    return h2_python(munged_file, output_dir)


def h2_python(munged_file, output_dir):
    """Approximate h2 from chi2 statistics."""
    try:
        if munged_file.endswith(".gz"):
            with gzip.open(munged_file, "rt") as f:
                df = pd.read_csv(f, sep="\t")
        else:
            df = pd.read_csv(munged_file, sep="\t")
    except Exception as e:
        print(f"ERROR reading {munged_file}: {e}")
        return None
    z_col = "Z" if "Z" in df.columns else None
    n_col = "N" if "N" in df.columns else None
    if not z_col:
        print("ERROR: no Z column in munged sumstats")
        return None
    n = int(df[n_col].median()) if n_col else 10000
    chi2 = df[z_col].astype(float) ** 2
    mean_chi2 = chi2.mean()
    # LDSC intercept approximation: intercept ≈ 1 + (mean_chi2 - 1) * correction
    # h2 ≈ (mean_chi2 - 1) / (n * ld_score_mean / num_snps)
    # Simplified: h2 ≈ (mean_chi2 - 1) / (n / num_snps) * correction
    num_snps = len(df)
    # Basic approximation (not accounting for LD)
    h2_approx = (mean_chi2 - 1) * num_snps / n
    h2_approx = max(0, min(1, h2_approx))
    intercept = max(1, mean_chi2 - h2_approx * n / num_snps)
    result = {"h2_observed": float(h2_approx), "mean_chi2": float(mean_chi2),
              "intercept": float(intercept), "n_snps": int(num_snps),
              "n_samples": int(n), "note": "Python approximation (no LD scores)"}
    result_path = os.path.join(output_dir, "h2_results.json")
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"SNP h2 (approx): {h2_approx:.4f}")
    print(f"Mean chi2: {mean_chi2:.4f}")
    print(f"Intercept: {intercept:.4f}")
    print(f"NOTE: Install LDSC for accurate h2 with LD score regression.")
    return result_path


# ---- Partitioned h2 ----
def h2_partitioned(munged_file, ld_annot_dir, output_dir):
    """Partitioned heritability by functional annotation."""
    os.makedirs(output_dir, exist_ok=True)
    if LDSC_BIN and ld_annot_dir:
        out_prefix = os.path.join(output_dir, "partitioned")
        cmd = [PYTHON_BIN or "python3", LDSC_BIN,
               "--h2", munged_file,
               "--ref-ld-chr", os.path.join(ld_annot_dir, "baseline."),
               "--w-ld-chr", os.path.join(ld_annot_dir, "weights."),
               "--out", out_prefix, "--overlap-annot"]
        print("Running LDSC partitioned h2...")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            if r.returncode == 0:
                result_file = out_prefix + ".results"
                if os.path.isfile(result_file):
                    df = pd.read_csv(result_file, delim_whitespace=True)
                    print(f"Partitioned h2 results: {result_file}")
                    print(df[["Category", "Prop._SNPs", "Prop._h2", "Enrichment", "p"]].head(20).to_string())
                    return result_file
        except subprocess.TimeoutExpired:
            print("LDSC partitioned h2 timed out")
    print("Partitioned h2 requires LDSC + annotation files.")
    print("Install: conda install -c bioconda ldsc")
    print("Download annotations: https://data.broadinstitute.org/alkesgroup/LDSCORE/")
    return None


# ---- Genetic correlation ----
def rg_estimate(munged1, munged2, output_dir, ld_ref=None):
    """Estimate bivariate genetic correlation."""
    os.makedirs(output_dir, exist_ok=True)
    if LDSC_BIN and ld_ref:
        out_prefix = os.path.join(output_dir, "rg_results")
        cmd = [PYTHON_BIN or "python3", LDSC_BIN,
               "--rg", f"{munged1},{munged2}",
               "--ref-ld-chr", os.path.join(ld_ref, "w_hm3."),
               "--w-ld-chr", os.path.join(ld_ref, "w_hm3."),
               "--out", out_prefix]
        print("Running LDSC --rg...")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
            if r.returncode == 0:
                log_file = out_prefix + ".log"
                if os.path.isfile(log_file):
                    with open(log_file) as f:
                        print(f.read()[:2000])
                    return log_file
        except subprocess.TimeoutExpired:
            print("LDSC rg timed out")
    # Fallback: Python approximation
    print("LDSC not available. Running Python rg approximation...")
    return rg_python(munged1, munged2, output_dir)


def rg_python(munged1, munged2, output_dir):
    """Approximate genetic correlation from Z-score correlation."""
    def load_z(f):
        if f.endswith(".gz"):
            with gzip.open(f, "rt") as fh:
                return pd.read_csv(fh, sep="\t")
        return pd.read_csv(f, sep="\t")
    df1 = load_z(munged1)
    df2 = load_z(munged2)
    merged = df1.merge(df2, on="SNP", suffixes=("_1", "_2"))
    if len(merged) < 100:
        print(f"ERROR: only {len(merged)} shared SNPs")
        return None
    from scipy.stats import pearsonr
    r, p = pearsonr(merged["Z_1"], merged["Z_2"])
    result = {"rg_approx": float(r), "p_value": float(p), "n_shared_snps": int(len(merged)),
              "note": "Python approximation (Z-score correlation, not LDSC)"}
    result_path = os.path.join(output_dir, "rg_results.json")
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Genetic correlation (approx): r = {r:.4f} (p = {p:.2e})")
    print(f"Shared SNPs: {len(merged)}")
    print("NOTE: This is Z-score correlation, not true LDSC rg.")
    return result_path


# ---- Pipeline ----
def pipeline_full(args):
    """Full heritability pipeline."""
    os.makedirs(args.output, exist_ok=True)
    print("=== Step 1: Munge Sumstats ===")
    munged = munge_sumstats(args.sumstats, os.path.join(args.output, "munge"), args.n)
    if not munged:
        return
    print("\n=== Step 2: h2 Estimation ===")
    h2_estimate(munged, os.path.join(args.output, "h2"), args.ld_ref)
    print(f"\n=== Heritability Analysis Complete ===")
    print(f"  Results: {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Population Heritability & LDSC")
    sub = parser.add_subparsers(dest="module", required=True)

    # pipeline
    p_pipe = sub.add_parser("pipeline")
    p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full")
    p_full.add_argument("--sumstats", required=True)
    p_full.add_argument("--output", required=True)
    p_full.add_argument("--ld-ref", help="LD reference panel directory")
    p_full.add_argument("--n", type=int, help="Sample size")

    # munge
    p_mg = sub.add_parser("munge")
    p_mg_sub = p_mg.add_subparsers(dest="subcommand", required=True)
    p_mr = p_mg_sub.add_parser("run")
    p_mr.add_argument("--sumstats", required=True)
    p_mr.add_argument("--output", required=True)
    p_mr.add_argument("--n", type=int)
    p_mr.add_argument("--chi2-threshold", type=float, default=0.001)

    # h2
    p_h2 = sub.add_parser("h2")
    p_h2_sub = p_h2.add_subparsers(dest="subcommand", required=True)
    p_he = p_h2_sub.add_parser("estimate")
    p_he.add_argument("--sumstats", required=True, help="Munged sumstats")
    p_he.add_argument("--output", required=True)
    p_he.add_argument("--ld-ref")
    p_hp = p_h2_sub.add_parser("partitioned")
    p_hp.add_argument("--sumstats", required=True)
    p_hp.add_argument("--ld-annot", required=True, help="LD annotation directory")
    p_hp.add_argument("--output", required=True)

    # rg
    p_rg = sub.add_parser("rg")
    p_rg_sub = p_rg.add_subparsers(dest="subcommand", required=True)
    p_re = p_rg_sub.add_parser("estimate")
    p_re.add_argument("--sumstats1", required=True)
    p_re.add_argument("--sumstats2", required=True)
    p_re.add_argument("--output", required=True)
    p_re.add_argument("--ld-ref")

    args = parser.parse_args()

    if args.module == "pipeline" and args.subcommand == "full":
        pipeline_full(args)
    elif args.module == "munge" and args.subcommand == "run":
        munge_sumstats(args.sumstats, args.output, args.n, args.chi2_threshold)
    elif args.module == "h2":
        if args.subcommand == "estimate":
            h2_estimate(args.sumstats, args.output, args.ld_ref)
        elif args.subcommand == "partitioned":
            h2_partitioned(args.sumstats, args.ld_annot, args.output)
    elif args.module == "rg" and args.subcommand == "estimate":
        rg_estimate(args.sumstats1, args.sumstats2, args.output, args.ld_ref)


if __name__ == "__main__":
    if not LDSC_BIN:
        print("NOTE: LDSC not found. Will use Python approximations.")
        print("Install: conda install -c bioconda ldsc")
    main()
