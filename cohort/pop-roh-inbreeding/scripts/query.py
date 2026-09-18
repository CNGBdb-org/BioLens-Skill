#!/usr/bin/env python3
"""
Population ROH & Inbreeding — query.py
=======================================
ROH 检测 + 近交系数 F 计算。

依赖: PLINK 1.9+, pandas, numpy, matplotlib
"""
import argparse, os, sys, shutil, subprocess, json
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

def run_plink(args):
    if not PLINK_BIN: return 1, "PLINK not found"
    cmd = [PLINK_BIN] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired: return 1, "TIMEOUT"

# Autosome length (GRCh38)
AUTOSOME_LENGTH = 2_881_530_672  # total autosomal bp for GRCh38

# ---- ROH detection ----
def roh_detect(prefix, output_dir, min_snp=50, min_kb=100, max_kb=5000, gap=1000, density=50):
    os.makedirs(output_dir, exist_ok=True)
    out_prefix = os.path.join(output_dir, "roh")
    rc, out_text = run_plink([
        "--bfile", prefix, "--homozyg",
        "--homozyg-snp", str(min_snp),
        "--homozyg-kb", str(min_kb),
        "--homozyg-density", str(density),
        "--homozyg-gap", str(gap),
        "--homozyg-window-snp", str(min_snp),
        "--homozyg-window-kb", str(min_kb),
        "--out", out_prefix,
    ])
    if rc != 0:
        print(f"ERROR: {out_text[:500]}")
        return None
    roh_file = out_prefix + ".hom"
    if not os.path.isfile(roh_file):
        print(f"ERROR: ROH file not found: {roh_file}")
        return None
    roh = pd.read_csv(roh_file, delim_whitespace=True)
    n_samples = roh["IID"].nunique()
    n_roh = len(roh)
    print(f"ROH: {n_roh} segments in {n_samples} individuals")
    print(f"  Mean length: {roh['KB'].astype(float).mean():.1f} kb")
    return roh_file

# ---- F(ROH) ----
def calc_f_roh(roh_file, output_dir, genome_length=AUTOSOME_LENGTH):
    os.makedirs(output_dir, exist_ok=True)
    roh = pd.read_csv(roh_file, delim_whitespace=True)
    f_vals = roh.groupby("IID").agg(
        total_roh_kb=("KB", "sum"), n_roh=("KB", "count"),
        longest_roh_kb=("KB", "max"), mean_roh_kb=("KB", "mean")
    ).reset_index()
    f_vals["F_ROH"] = (f_vals["total_roh_kb"] * 1000) / genome_length
    # Classify by length
    f_vals["short_roh"] = roh[roh["KB"] < 500].groupby("IID").size().reindex(f_vals["IID"], fill_value=0).values
    f_vals["long_roh"] = roh[roh["KB"] >= 1500].groupby("IID").size().reindex(f_vals["IID"], fill_value=0).values
    result_file = os.path.join(output_dir, "f_roh.tsv")
    f_vals.to_csv(result_file, sep="\t", index=False)
    print(f"F(ROH): {len(f_vals)} individuals")
    print(f"  Mean F(ROH): {f_vals['F_ROH'].mean():.4f}")
    print(f"  Range: {f_vals['F_ROH'].min():.4f} - {f_vals['F_ROH'].max():.4f}")
    return result_file

# ---- Fhat (PLINK) ----
def calc_fhat(prefix, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    out_prefix = os.path.join(output_dir, "fhat")
    rc, out_text = run_plink(["--bfile", prefix, "--het", "--out", out_prefix])
    if rc != 0:
        print(f"ERROR: {out_text[:500]}")
        return None
    het_file = out_prefix + ".het"
    if not os.path.isfile(het_file):
        return None
    het = pd.read_csv(het_file, delim_whitespace=True)
    het["F"] = het["F"].astype(float)
    print(f"Fhat: {len(het)} individuals, mean F = {het['F'].mean():.4f}")
    result_file = os.path.join(output_dir, "fhat.tsv")
    het.to_csv(result_file, sep="\t", index=False)
    return result_file

# ---- Plot ----
def plot_distribution(roh_file, output):
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib not installed"); return
    roh = pd.read_csv(roh_file, delim_whitespace=True)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    # ROH length distribution
    ax1.hist(roh["KB"].astype(float), bins=50, edgecolor="black", alpha=0.7)
    ax1.set_xlabel("ROH length (kb)")
    ax1.set_ylabel("Count")
    ax1.set_title("ROH Length Distribution")
    # F(ROH) distribution
    f_vals = roh.groupby("IID")["KB"].sum().reset_index()
    f_vals["F"] = f_vals["KB"] * 1000 / AUTOSOME_LENGTH
    ax2.hist(f_vals["F"], bins=50, edgecolor="black", alpha=0.7, color="coral")
    ax2.set_xlabel("F(ROH)")
    ax2.set_ylabel("Count")
    ax2.set_title("Inbreeding Coefficient Distribution")
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print(f"Distribution plot saved: {output}")

# ---- Pipeline ----
def pipeline_full(args):
    os.makedirs(args.output, exist_ok=True)
    print("=== Step 1: ROH Detection ===")
    roh_file = roh_detect(args.input, os.path.join(args.output, "roh"), args.min_snp, args.min_kb, args.max_kb, args.gap, args.density)
    if not roh_file: return
    print("\n=== Step 2: F(ROH) ===")
    calc_f_roh(roh_file, os.path.join(args.output, "f_roh"))
    print("\n=== Step 3: Fhat ===")
    calc_fhat(args.input, os.path.join(args.output, "fhat"))
    print("\n=== Step 4: Plot ===")
    plot_distribution(roh_file, os.path.join(args.output, "roh_distribution.png"))
    print(f"\n=== ROH & Inbreeding Complete ===")
    print(f"  Results: {args.output}")

def main():
    parser = argparse.ArgumentParser(description="Population ROH & Inbreeding")
    sub = parser.add_subparsers(dest="module", required=True)
    p_pipe = sub.add_parser("pipeline"); p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full")
    p_full.add_argument("--input", required=True); p_full.add_argument("--output", required=True)
    p_full.add_argument("--min-snp", type=int, default=50); p_full.add_argument("--min-kb", type=int, default=100)
    p_full.add_argument("--max-kb", type=int, default=5000); p_full.add_argument("--gap", type=int, default=1000)
    p_full.add_argument("--density", type=int, default=50)
    p_roh = sub.add_parser("roh"); p_roh_sub = p_roh.add_subparsers(dest="subcommand", required=True)
    p_rd = p_roh_sub.add_parser("detect")
    p_rd.add_argument("--input", required=True); p_rd.add_argument("--output", required=True)
    p_rd.add_argument("--min-snp", type=int, default=50); p_rd.add_argument("--min-kb", type=int, default=100)
    p_rd.add_argument("--max-kb", type=int, default=5000); p_rd.add_argument("--gap", type=int, default=1000)
    p_rd.add_argument("--density", type=int, default=50)
    p_f = sub.add_parser("f"); p_f_sub = p_f.add_subparsers(dest="subcommand", required=True)
    p_fc = p_f_sub.add_parser("calc")
    p_fc.add_argument("--roh", required=True); p_fc.add_argument("--output", required=True)
    p_fh = sub.add_parser("fhat"); p_fh_sub = p_fh.add_subparsers(dest="subcommand", required=True)
    p_fhc = p_fh_sub.add_parser("calc")
    p_fhc.add_argument("--input", required=True); p_fhc.add_argument("--output", required=True)
    p_pl = sub.add_parser("plot"); p_pl_sub = p_pl.add_subparsers(dest="subcommand", required=True)
    p_pd = p_pl_sub.add_parser("distribution")
    p_pd.add_argument("--roh", required=True); p_pd.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.module == "pipeline" and args.subcommand == "full": pipeline_full(args)
    elif args.module == "roh" and args.subcommand == "detect":
        roh_detect(args.input, args.output, args.min_snp, args.min_kb, args.max_kb, args.gap, args.density)
    elif args.module == "f" and args.subcommand == "calc": calc_f_roh(args.roh, args.output)
    elif args.module == "fhat" and args.subcommand == "calc": calc_fhat(args.input, args.output)
    elif args.module == "plot" and args.subcommand == "distribution": plot_distribution(args.roh, args.output)

if __name__ == "__main__":
    if not PLINK_BIN: print("WARNING: PLINK not found.")
    main()
