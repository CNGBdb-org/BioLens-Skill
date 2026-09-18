#!/usr/bin/env python3
"""
Population LD & Haplotype — query.py
=====================================
LD 衰减 + LD 矩阵 + LD 剪枝 + 单倍型频率。

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

# ---- LD decay ----
def ld_decay(prefix, output_dir, max_dist=500, bin_size=10):
    """Compute LD decay: mean r2 by distance bins."""
    os.makedirs(output_dir, exist_ok=True)
    out_prefix = os.path.join(output_dir, "ld_decay")
    rc, out_text = run_plink([
        "--bfile", prefix, "--r2", "interchr", "--ld-window-r2", "0",
        "--ld-window", "999999", "--ld-window-kb", str(max_dist),
        "--out", out_prefix
    ])
    if rc != 0:
        print(f"ERROR: {out_text[:500]}")
        return None
    ld_file = out_prefix + ".ld"
    if not os.path.isfile(ld_file):
        print("ERROR: LD file not found")
        return None
    ld = pd.read_csv(ld_file, delim_whitespace=True)
    if "R2" not in ld.columns or "BP_A" not in ld.columns or "BP_B" not in ld.columns:
        print("ERROR: missing columns in LD file")
        return None
    ld["dist_kb"] = (ld["BP_B"].astype(int) - ld["BP_A"].astype(int)).abs() / 1000
    ld = ld[ld["dist_kb"] <= max_dist]
    ld["bin"] = (ld["dist_kb"] // bin_size * bin_size).astype(int)
    decay = ld.groupby("bin").agg(mean_r2=("R2", "mean"), n_pairs=("R2", "count")).reset_index()
    result_file = os.path.join(output_dir, "ld_decay.tsv")
    decay.to_csv(result_file, sep="\t", index=False)
    print(f"LD decay: {len(decay)} bins (max {max_dist}kb, bin {bin_size}kb)")
    if len(decay) > 0:
        print(f"  r2 at 0kb: {decay['mean_r2'].iloc[0]:.4f}")
        print(f"  r2 at {max_dist}kb: {decay['mean_r2'].iloc[-1]:.4f}")
    return result_file

# ---- LD matrix ----
def ld_matrix(prefix, region, output_dir):
    """Compute LD matrix for a specific region."""
    os.makedirs(output_dir, exist_ok=True)
    parts = region.replace("chr","").split(":")
    chrom = parts[0]
    start, end = map(int, parts[1].split("-"))
    range_str = f"{chrom}:{start}-{end}"
    out_prefix = os.path.join(output_dir, "ld_matrix")
    rc, out_text = run_plink([
        "--bfile", prefix, "--chr", str(chrom),
        "--from-bp", str(start), "--to-bp", str(end),
        "--r", "square", "--keep-allele-order", "--out", out_prefix
    ])
    if rc != 0:
        print(f"ERROR: {out_text[:500]}")
        return None
    ld_file = out_prefix + ".ld"
    bim_file = out_prefix + ".bim"
    if os.path.isfile(ld_file) and os.path.isfile(bim_file):
        n = sum(1 for _ in open(bim_file))
        print(f"LD matrix: {n}x{n} for chr{chrom}:{start}-{end}")
        return ld_file
    print("ERROR: LD matrix not found")
    return None

# ---- LD pruning ----
def ld_prune(prefix, output_dir, window=50, step=5, r2=0.2):
    """LD pruning to get independent SNPs."""
    os.makedirs(output_dir, exist_ok=True)
    out_prefix = os.path.join(output_dir, "prune")
    rc, out_text = run_plink([
        "--bfile", prefix, "--indep-pairwise",
        str(window), str(step), str(r2), "--out", out_prefix
    ])
    if rc != 0:
        print(f"ERROR: {out_text[:500]}")
        return None
    prune_in = out_prefix + ".prune.in"
    if os.path.isfile(prune_in):
        n = sum(1 for _ in open(prune_in))
        print(f"LD pruning: {n} independent SNPs (window={window}, step={step}, r2={r2})")
        return prune_in
    return None

# ---- Haplotype frequency ----
def haplotype_freq(prefix, output_dir, region=None):
    """Estimate haplotype frequencies using PLINK blocks."""
    os.makedirs(output_dir, exist_ok=True)
    out_prefix = os.path.join(output_dir, "haplotype")
    cmd = ["--bfile", prefix, "--blocks", "--out", out_prefix]
    if region:
        parts = region.replace("chr","").split(":")
        cmd += ["--chr", parts[0]]
    rc, out_text = run_plink(cmd)
    if rc != 0:
        print(f"ERROR: {out_text[:500]}")
        return None
    block_file = out_prefix + ".blocks"
    freq_file = out_prefix + ".blocks.freqs"
    if os.path.isfile(freq_file):
        freq = pd.read_csv(freq_file, delim_whitespace=True)
        print(f"Haplotype frequencies: {len(freq)} haplotypes")
        return freq_file
    print("No haplotype blocks detected")
    return None

# ---- Plot ----
def plot_decay(decay_file, output):
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib not installed"); return
    decay = pd.read_csv(decay_file, sep="\t")
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(decay["bin"], decay["mean_r2"], "o-", markersize=3, linewidth=1.5)
    ax.set_xlabel("Distance (kb)")
    ax.set_ylabel("Mean r2")
    ax.set_title("LD Decay")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    print(f"LD decay plot saved: {output}")

# ---- Pipeline ----
def pipeline_full(args):
    os.makedirs(args.output, exist_ok=True)
    print("=== Step 1: LD Decay ===")
    decay_file = ld_decay(args.input, os.path.join(args.output, "decay"), args.max_dist, args.bin_size)
    print("\n=== Step 2: LD Pruning ===")
    ld_prune(args.input, os.path.join(args.output, "prune"), args.window, args.step, args.r2)
    if decay_file:
        print("\n=== Step 3: Plot ===")
        plot_decay(decay_file, os.path.join(args.output, "ld_decay.png"))
    print(f"\n=== LD Analysis Complete ===")
    print(f"  Results: {args.output}")

def main():
    parser = argparse.ArgumentParser(description="Population LD & Haplotype")
    sub = parser.add_subparsers(dest="module", required=True)
    p_pipe = sub.add_parser("pipeline"); p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full")
    p_full.add_argument("--input", required=True); p_full.add_argument("--output", required=True)
    p_full.add_argument("--max-dist", type=int, default=500); p_full.add_argument("--bin-size", type=int, default=10)
    p_full.add_argument("--r2", type=float, default=0.2); p_full.add_argument("--window", type=int, default=50)
    p_full.add_argument("--step", type=int, default=5)
    p_dec = sub.add_parser("decay"); p_dec_sub = p_dec.add_subparsers(dest="subcommand", required=True)
    p_dc = p_dec_sub.add_parser("compute")
    p_dc.add_argument("--input", required=True); p_dc.add_argument("--output", required=True)
    p_dc.add_argument("--max-dist", type=int, default=500); p_dc.add_argument("--bin-size", type=int, default=10)
    p_mat = sub.add_parser("matrix"); p_mat_sub = p_mat.add_subparsers(dest="subcommand", required=True)
    p_mc = p_mat_sub.add_parser("compute")
    p_mc.add_argument("--input", required=True); p_mc.add_argument("--region", required=True)
    p_mc.add_argument("--output", required=True)
    p_pr = sub.add_parser("prune"); p_pr_sub = p_pr.add_subparsers(dest="subcommand", required=True)
    p_pr_r = p_pr_sub.add_parser("run")
    p_pr_r.add_argument("--input", required=True); p_pr_r.add_argument("--output", required=True)
    p_pr_r.add_argument("--r2", type=float, default=0.2); p_pr_r.add_argument("--window", type=int, default=50)
    p_pr_r.add_argument("--step", type=int, default=5)
    p_ha = sub.add_parser("haplotype"); p_ha_sub = p_ha.add_subparsers(dest="subcommand", required=True)
    p_hf = p_ha_sub.add_parser("freq")
    p_hf.add_argument("--input", required=True); p_hf.add_argument("--output", required=True)
    p_hf.add_argument("--region")
    p_pl = sub.add_parser("plot"); p_pl_sub = p_pl.add_subparsers(dest="subcommand", required=True)
    p_pd = p_pl_sub.add_parser("decay")
    p_pd.add_argument("--data", required=True); p_pd.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.module == "pipeline" and args.subcommand == "full": pipeline_full(args)
    elif args.module == "decay" and args.subcommand == "compute":
        ld_decay(args.input, args.output, args.max_dist, args.bin_size)
    elif args.module == "matrix" and args.subcommand == "compute":
        ld_matrix(args.input, args.region, args.output)
    elif args.module == "prune" and args.subcommand == "run":
        ld_prune(args.input, args.output, args.window, args.step, args.r2)
    elif args.module == "haplotype" and args.subcommand == "freq":
        haplotype_freq(args.input, args.output, args.region)
    elif args.module == "plot" and args.subcommand == "decay":
        plot_decay(args.data, args.output)

if __name__ == "__main__":
    if not PLINK_BIN: print("WARNING: PLINK not found.")
    main()
