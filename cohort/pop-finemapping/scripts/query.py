#!/usr/bin/env python3
"""
Population Fine-Mapping — query.py
===================================
GWAS locus 精细定位：SuSiE / FINEMAP / CAVIAR。
计算 PIP、credible set、locus zoom plot。

依赖: pandas, numpy, matplotlib
可选: R+susieR, FINEMAP, CAVIAR
"""
import argparse
import os
import sys
import shutil
import subprocess
import json
import tempfile
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
FINEMAP_BIN = shutil.which("finemap") or shutil.which("FINEMAP")
CAVIAR_BIN = shutil.which("caviar") or shutil.which("CAVIAR")

def find_rscript():
    for d in [os.path.expanduser("~/software/miniforge/envs/cima/bin"),
              os.path.expanduser("~/software/miniforge/bin"),
              "/usr/bin", "/usr/local/bin"]:
        fp = os.path.join(d, "Rscript")
        if os.path.isfile(fp) and os.access(fp, os.X_OK): return fp
    return shutil.which("Rscript")


# ---- Locus extraction ----
def extract_locus(sumstats, locus_str, flank=500000):
    """Extract variants in locus region from sumstats."""
    parts = locus_str.replace("chr", "").split(":")
    chrom = parts[0]
    if "-" in parts[1]:
        start, end = map(int, parts[1].split("-"))
    else:
        center = int(parts[1])
        start, end = center - flank, center + flank
    df = pd.read_csv(sumstats, delim_whitespace=True)
    chr_col = next((c for c in ["CHR", "CHROM", "chr"] if c in df.columns), None)
    pos_col = next((c for c in ["BP", "POS", "pos"] if c in df.columns), None)
    if not chr_col or not pos_col:
        print(f"ERROR: need CHR and BP columns. Found: {list(df.columns)}")
        return None
    mask = (df[chr_col].astype(str) == str(chrom)) & \
           (df[pos_col].astype(int) >= start) & (df[pos_col].astype(int) <= end)
    locus_df = df[mask].copy()
    print(f"Locus chr{chrom}:{start}-{end}: {len(locus_df)} variants")
    return locus_df, chrom, start, end


# ---- LD matrix ----
def compute_ld(ld_ref, snp_list, output_dir):
    """Compute LD matrix for given SNPs from reference panel."""
    snp_file = os.path.join(output_dir, "locus_snps.txt")
    with open(snp_file, "w") as f:
        f.write("\n".join(snp_list))
    ld_prefix = os.path.join(output_dir, "ld_matrix")
    if PLINK_BIN:
        cmd = [PLINK_BIN, "--bfile", ld_ref, "--extract", snp_file,
               "--r", "square", "--keep-allele-order",
               "--out", ld_prefix]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if r.returncode == 0 and os.path.isfile(ld_prefix + ".ld"):
            print(f"LD matrix computed: {ld_prefix}.ld")
            return ld_prefix + ".ld"
    print("WARNING: could not compute LD matrix. Using identity matrix.")
    return None


# ---- SuSiE ----
def run_susie(locus_df, ld_matrix_file, output_dir, credible_level=0.95, max_causal=10):
    """Run SuSiE fine-mapping via R susieR."""
    rscript = find_rscript()
    if not rscript:
        print("Rscript not found. Install R + susieR:")
        print("  conda install -c conda-forge r-susier")
        return run_python_pip(locus_df, ld_matrix_file, output_dir, credible_level)
    os.makedirs(output_dir, exist_ok=True)
    # Prepare input files
    z_file = os.path.join(output_dir, "z_scores.txt")
    ld_file = ld_matrix_file or os.path.join(output_dir, "identity_ld.txt")
    if not ld_matrix_file:
        n = len(locus_df)
        np.savetxt(ld_file, np.eye(n), fmt="%.6f")
    # Z-scores from BETA and P
    from scipy.stats import norm
    beta_col = next((c for c in ["BETA", "OR"] if c in locus_df.columns), "BETA")
    pval_col = next((c for c in ["P", "PVAL"] if c in locus_df.columns), "P")
    se_col = next((c for c in ["SE"] if c in locus_df.columns), None)
    if se_col and beta_col == "BETA":
        z = locus_df[beta_col].astype(float) / locus_df[se_col].astype(float)
    else:
        # Z from p-value
        z = locus_df[pval_col].astype(float).apply(
            lambda p: norm.ppf(p / 2) * (-1 if p > 0 else 1))
    np.savetxt(z_file, z.values, fmt="%.6f")
    # R script
    r_script = f"""
library(susieR)
z <- as.numeric(readLines("{z_file}"))
R <- as.matrix(read.table("{ld_file}"))
n <- length(z)
fit <- susie_rss(z, R, L = {max_causal})
pip <- susie_get_pip(fit)
cs <- susie_get_cs(fit, coverage = {credible_level}, min_abs_corr = 0.5)
out_pip <- data.frame(SNP = seq_len(n), PIP = pip)
write.table(out_pip, "{os.path.join(output_dir, 'susie_pip.txt')}", row.names=FALSE, quote=FALSE)
if (length(cs$cs) > 0) {{
  for (i in seq_along(cs$cs)) {{
    cat(paste("CS", i, ":", paste(cs$cs[[i]], collapse=","), "\\n"))
  }}
}} else {{
  cat("No credible set found\\n")
}}
saveRDS(fit, "{os.path.join(output_dir, 'susie_fit.rds')}")
cat("SuSiE complete\\n")
"""
    r_file = os.path.join(output_dir, "run_susie.R")
    with open(r_file, "w") as f:
        f.write(r_script)
    print("Running SuSiE (susieR)...")
    try:
        r = subprocess.run([rscript, r_file], capture_output=True, text=True, timeout=7200)
        if r.returncode != 0:
            print(f"SuSiE R failed: {r.stderr[:500]}")
            return run_python_pip(locus_df, ld_matrix_file, output_dir, credible_level)
        print(r.stdout)
        pip_file = os.path.join(output_dir, "susie_pip.txt")
        if os.path.isfile(pip_file):
            pip_df = pd.read_csv(pip_file, delim_whitespace=True)
            locus_df = locus_df.reset_index(drop=True)
            locus_df["PIP"] = pip_df["PIP"].values
            locus_df = locus_df.sort_values("PIP", ascending=False)
            result_file = os.path.join(output_dir, "finemap_results.tsv")
            locus_df.to_csv(result_file, sep="\t", index=False)
            print(f"SuSiE results: {result_file}")
            print(f"Top 5 PIP:")
            print(locus_df.head(5)[["SNP", "PIP"]].to_string(index=False))
            return result_file
    except subprocess.TimeoutExpired:
        print("SuSiE timed out")
    return run_python_pip(locus_df, ld_matrix_file, output_dir, credible_level)


def run_python_pip(locus_df, ld_matrix_file, output_dir, credible_level=0.95):
    """Fallback: simple PIP approximation from p-values (no Bayesian model)."""
    print("Using simple PIP approximation (install susieR for full Bayesian fine-mapping)")
    from scipy.stats import norm
    pval_col = next((c for c in ["P", "PVAL"] if c in locus_df.columns), "P")
    # Bayes factor approximation: -log10(p) as proxy
    log10p = -np.log10(locus_df[pval_col].astype(float).clip(lower=1e-300))
    # Soft-max style PIP
    weights = np.exp(log10p - log10p.max())
    pip = weights / weights.sum()
    locus_df = locus_df.copy()
    locus_df["PIP"] = pip.values
    locus_df = locus_df.sort_values("PIP", ascending=False)
    # Credible set
    cumsum = locus_df["PIP"].cumsum()
    credible_idx = cumsum <= credible_level
    locus_df["in_credible_set"] = credible_idx
    result_file = os.path.join(output_dir, "finemap_results.tsv")
    locus_df.to_csv(result_file, sep="\t", index=False)
    n_cs = credible_idx.sum()
    print(f"Simple PIP approximation: {n_cs} variants in {int(credible_level*100)}% credible set")
    print(f"Results: {result_file}")
    return result_file


# ---- FINEMAP ----
def run_finemap(locus_df, ld_ref, chrom, start, end, output_dir, max_causal=10):
    """Run FINEMAP fine-mapping."""
    if not FINEMAP_BIN:
        print("FINEMAP not found. Install: http://www.christianbenner.com/")
        print("Falling back to SuSiE...")
        ld_file = compute_ld(ld_ref, locus_df["SNP"].tolist(), output_dir) if ld_ref else None
        return run_susie(locus_df, ld_file, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    # Prepare input files (FINEMAP format: SNP CHR BP A1 A2 MAF BETA SE P)
    master_file = os.path.join(output_dir, "finemap.master")
    z_file = os.path.join(output_dir, "finemap.z")
    ld_file = os.path.join(output_dir, "finemap.ld")
    # Write z file
    snp_col = "SNP" if "SNP" in locus_df.columns else "rsID"
    out_cols = [snp_col]
    locus_df[[snp_col]].to_csv(z_file, sep=" ", index=False, header=False)
    # Write master
    with open(master_file, "w") as f:
        f.write(f"z;ld;snp;config;cred;log;n-causal-snps\n")
        f.write(f"{z_file};{ld_file};{os.path.join(output_dir, 'finemap_snp')};"
                f"{os.path.join(output_dir, 'finemap_config')};"
                f"{os.path.join(output_dir, 'finemap_cred')};"
                f"{os.path.join(output_dir, 'finemap_log')};1;{max_causal}\n")
    cmd = [FINEMAP_BIN, "--sss", "--in-files", master_file, "--n-causal-snps", str(max_causal)]
    print("Running FINEMAP...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if r.returncode != 0:
            print(f"FINEMAP failed: {r.stderr[:500]}")
            return run_susie(locus_df, None, output_dir)
    except subprocess.TimeoutExpired:
        print("FINEMAP timed out")
        return run_susie(locus_df, None, output_dir)
    # Parse results
    snp_file = os.path.join(output_dir, "finemap_snp")
    if os.path.isfile(snp_file):
        result = pd.read_csv(snp_file, delim_whitespace=True)
        print(f"FINEMAP complete: {result_file}")
        return snp_file
    print("FINEMAP results not found")
    return run_susie(locus_df, None, output_dir)


# ---- CAVIAR ----
def run_caviar(locus_df, ld_ref, output_dir, max_causal=10):
    """Run CAVIAR fine-mapping."""
    if not CAVIAR_BIN:
        print("CAVIAR not found. Install: http://csg.sph.umich.edu/abecasis/CAVIAR/")
        print("Falling back to SuSiE...")
        return run_susie(locus_df, None, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    z_file = os.path.join(output_dir, "caviar_z.txt")
    ld_file = os.path.join(output_dir, "caviar_ld.txt")
    out_prefix = os.path.join(output_dir, "caviar_out")
    # Write z-scores
    from scipy.stats import norm
    pval_col = next((c for c in ["P", "PVAL"] if c in locus_df.columns), "P")
    z = locus_df[pval_col].astype(float).apply(lambda p: norm.ppf(p / 2))
    np.savetxt(z_file, z.values, fmt="%.6f")
    cmd = [CAVIAR_BIN, "-z", z_file, "-l", ld_file, "-o", out_prefix, "-c", str(max_causal)]
    print("Running CAVIAR...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if r.returncode != 0:
            print(f"CAVIAR failed: {r.stderr[:500]}")
            return run_susie(locus_df, None, output_dir)
    except subprocess.TimeoutExpired:
        print("CAVIAR timed out")
        return run_susie(locus_df, None, output_dir)
    # Parse results
    pip_file = out_prefix + "_post"
    if os.path.isfile(pip_file):
        pip = pd.read_csv(pip_file, delim_whitespace=True, header=None, names=["SNP_idx", "PIP"])
        locus_df = locus_df.reset_index(drop=True)
        locus_df["PIP"] = pip["PIP"].values
        result_file = os.path.join(output_dir, "finemap_results.tsv")
        locus_df.to_csv(result_file, sep="\t", index=False)
        print(f"CAVIAR complete: {result_file}")
        return result_file
    print("CAVIAR results not found")
    return run_susie(locus_df, None, output_dir)


# ---- LocusZoom plot ----
def plot_locuszoom(sumstats_file, pip_file, output, locus=None):
    """Generate locus zoom plot with PIP coloring."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib not installed")
        return
    df = pd.read_csv(pip_file, sep="\t")
    pos_col = next((c for c in ["BP", "POS"] if c in df.columns), None)
    pip_col = "PIP" if "PIP" in df.columns else None
    if not pos_col or not pip_col:
        print("ERROR: need BP and PIP columns")
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    # Color by PIP
    scatter = ax.scatter(df[pos_col], -np.log10(df.get("P", df[pip_col]).astype(float) + 1e-300) if "P" in df else df[pip_col],
                         c=df[pip_col], cmap="YlOrRd", s=20, edgecolors="black", linewidth=0.3)
    plt.colorbar(scatter, label="PIP")
    ax.set_xlabel("Position (bp)")
    ax.set_ylabel("-log10(P)" if "P" in df.columns else "PIP")
    ax.set_title(f"LocusZoom {locus or ''}")
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print(f"LocusZoom plot saved: {output}")


# ---- Pipeline ----
def pipeline_full(args):
    """Full fine-mapping pipeline."""
    os.makedirs(args.output, exist_ok=True)
    print("=== Step 1: Extract Locus ===")
    result = extract_locus(args.sumstats, args.locus, args.flank)
    if not result:
        return
    locus_df, chrom, start, end = result
    print("\n=== Step 2: Compute LD ===")
    ld_file = compute_ld(args.ld_ref, locus_df["SNP"].tolist(), args.output) if args.ld_ref else None
    print("\n=== Step 3: Fine-Mapping ===")
    if args.tool == "finemap":
        result_file = run_finemap(locus_df, args.ld_ref, chrom, start, end, args.output, args.max_causal)
    elif args.tool == "caviar":
        result_file = run_caviar(locus_df, args.ld_ref, args.output, args.max_causal)
    else:
        result_file = run_susie(locus_df, ld_file, args.output, args.credible_level, args.max_causal)
    if not result_file:
        return
    print("\n=== Step 4: LocusZoom Plot ===")
    plot_locuszoom(args.sumstats, result_file,
                   os.path.join(args.output, "locuszoom.png"), args.locus)
    print(f"\n=== Fine-Mapping Complete ===")
    print(f"  Results: {result_file}")
    print(f"  Plot: {os.path.join(args.output, 'locuszoom.png')}")


def main():
    parser = argparse.ArgumentParser(description="Population Fine-Mapping")
    sub = parser.add_subparsers(dest="module", required=True)

    # pipeline
    p_pipe = sub.add_parser("pipeline")
    p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full")
    add_full_args(p_full)

    # run
    p_run = sub.add_parser("run")
    p_run_sub = p_run.add_subparsers(dest="subcommand", required=True)
    for tool in ["susie", "finemap", "caviar"]:
        sp = p_run_sub.add_parser(tool)
        sp.add_argument("--sumstats", required=True)
        sp.add_argument("--ld-ref", required=True)
        sp.add_argument("--locus", required=True, help="chr:start-end")
        sp.add_argument("--output", required=True)
        sp.add_argument("--credible-level", type=float, default=0.95)
        sp.add_argument("--max-causal", type=int, default=10)
        sp.add_argument("--flank", type=int, default=500000)

    # plot
    p_plot = sub.add_parser("plot")
    p_plot_sub = p_plot.add_subparsers(dest="subcommand", required=True)
    p_lz = p_plot_sub.add_parser("locuszoom")
    p_lz.add_argument("--sumstats", required=True)
    p_lz.add_argument("--pip", required=True, help="PIP results file")
    p_lz.add_argument("--output", required=True)
    p_lz.add_argument("--locus", help="Locus label")

    args = parser.parse_args()

    if args.module == "pipeline" and args.subcommand == "full":
        pipeline_full(args)
    elif args.module == "run":
        result = extract_locus(args.sumstats, args.locus, args.flank)
        if not result:
            return
        locus_df, chrom, start, end = result
        ld_file = compute_ld(args.ld_ref, locus_df["SNP"].tolist(), args.output) if args.ld_ref else None
        if args.subcommand == "susie":
            run_susie(locus_df, ld_file, args.output, args.credible_level, args.max_causal)
        elif args.subcommand == "finemap":
            run_finemap(locus_df, args.ld_ref, chrom, start, end, args.output, args.max_causal)
        elif args.subcommand == "caviar":
            run_caviar(locus_df, args.ld_ref, args.output, args.max_causal)
    elif args.module == "plot" and args.subcommand == "locuszoom":
        plot_locuszoom(args.sumstats, args.pip, args.output, args.locus)


def add_full_args(p):
    p.add_argument("--sumstats", required=True)
    p.add_argument("--ld-ref", required=True, help="LD reference PLINK prefix")
    p.add_argument("--locus", required=True, help="chr:start-end")
    p.add_argument("--output", required=True)
    p.add_argument("--tool", default="susie", choices=["susie", "finemap", "caviar"])
    p.add_argument("--credible-level", type=float, default=0.95)
    p.add_argument("--max-causal", type=int, default=10)
    p.add_argument("--flank", type=int, default=500000)


if __name__ == "__main__":
    main()
