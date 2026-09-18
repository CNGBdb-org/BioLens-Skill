#!/usr/bin/env python3
"""
Population GWAS Visualization — query.py
=========================================
GWAS 综合可视化：Manhattan / QQ / Regional / Forest / Compare。

依赖: pandas, numpy, matplotlib
"""
import argparse, os, sys, json
import numpy as np
import pandas as pd

def detect_cols(df):
    chr_col = next((c for c in ["CHR","CHROM","chrom","chr"] if c in df.columns), None)
    pos_col = next((c for c in ["BP","POS","pos","position"] if c in df.columns), None)
    pval_col = next((c for c in ["P","PVAL","PVALUE","p","pval"] if c in df.columns), None)
    snp_col = next((c for c in ["SNP","rsID","MarkerName","snp"] if c in df.columns), None)
    beta_col = next((c for c in ["BETA","OR","Effect","beta"] if c in df.columns), None)
    se_col = next((c for c in ["SE","StdErr","se"] if c in df.columns), None)
    return chr_col, pos_col, pval_col, snp_col, beta_col, se_col

# ---- Manhattan ----
def plot_manhattan(sumstats_file, output, threshold=5e-8, highlight=None, dpi=150):
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib not installed"); return
    df = pd.read_csv(sumstats_file, delim_whitespace=True)
    chr_col, pos_col, pval_col, snp_col, *_ = detect_cols(df)
    if not all([chr_col, pos_col, pval_col]):
        print(f"ERROR: need CHR, BP, P. Found: {list(df.columns)}"); return
    df = df.dropna(subset=[chr_col, pos_col, pval_col]).copy()
    df["CHR_NUM"] = df[chr_col].astype(str).str.replace("chr","").str.replace("X","23").str.replace("Y","24")
    df = df[df["CHR_NUM"].str.match(r"^\d+$")].copy()
    df["CHR_NUM"] = df["CHR_NUM"].astype(int)
    df = df[df["CHR_NUM"] <= 22].sort_values(["CHR_NUM", pos_col])
    df["neglogp"] = -np.log10(df[pval_col].astype(float).clip(lower=1e-300))
    df["cum_pos"] = 0; offset = 0
    for chrom in sorted(df["CHR_NUM"].unique()):
        mask = df["CHR_NUM"] == chrom
        df.loc[mask, "cum_pos"] = df.loc[mask, pos_col].astype(int) + offset
        offset = df.loc[mask, "cum_pos"].max() + 5e6
    fig, ax = plt.subplots(figsize=(14, 5))
    colors = ["#1f77b4", "#ff7f0e"] * 11
    for chrom in sorted(df["CHR_NUM"].unique()):
        mask = df["CHR_NUM"] == chrom
        ax.scatter(df.loc[mask, "cum_pos"], df.loc[mask, "neglogp"],
                   s=2, c=colors[chrom-1], alpha=0.6)
    # Highlight
    if highlight and snp_col:
        hl_set = set(open(highlight).read().strip().split("\n")) if os.path.isfile(highlight) else set(highlight.split(","))
        hl_mask = df[snp_col].isin(hl_set)
        if hl_mask.any():
            ax.scatter(df.loc[hl_mask, "cum_pos"], df.loc[hl_mask, "neglogp"],
                       s=10, c="red", edgecolors="black", linewidth=0.5, label="Highlighted")
            ax.legend(fontsize=8)
    # Threshold lines
    ax.axhline(-np.log10(threshold), color="red", linestyle="--", lw=0.5, label=f"p={threshold}")
    ax.axhline(-np.log10(1e-5), color="blue", linestyle=":", lw=0.3, label="p=1e-5")
    # X-axis
    ticks = [(c, df[df["CHR_NUM"]==c]["cum_pos"].mean()) for c in sorted(df["CHR_NUM"].unique())]
    ax.set_xticks([t[1] for t in ticks]); ax.set_xticklabels([str(t[0]) for t in ticks], fontsize=7)
    ax.set_xlabel("Chromosome"); ax.set_ylabel("-log10(P)"); ax.set_title("Manhattan Plot")
    ax.legend(fontsize=8, loc="upper right")
    fig.tight_layout(); fig.savefig(output, dpi=dpi)
    n_sig = int((df[pval_col].astype(float) < threshold).sum())
    print(f"Manhattan plot: {output} ({len(df)} SNPs, {n_sig} significant)")
    return output

# ---- QQ plot ----
def plot_qq(sumstats_file, output, dpi=150):
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib not installed"); return
    df = pd.read_csv(sumstats_file, delim_whitespace=True)
    pval_col = next((c for c in ["P","PVAL","PVALUE","p"] if c in df.columns), None)
    if not pval_col:
        print("ERROR: no p-value column"); return
    pvals = df[pval_col].dropna().astype(float).sort_values().values
    n = len(pvals)
    expected = -np.log10(np.arange(1, n+1) / (n+1))
    observed = -np.log10(pvals)
    # Lambda GC
    chi2 = -2 * np.log(pvals)
    lambdagc = np.median(chi2) / 0.4549
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(expected, observed, s=1, alpha=0.5, c="steelblue")
    ax.plot([0, expected.max()], [0, expected.max()], "r--", lw=0.5)
    ax.set_xlabel("Expected -log10(P)"); ax.set_ylabel("Observed -log10(P)")
    ax.set_title(f"QQ Plot (λGC={lambdagc:.3f})")
    ax.text(0.05, 0.95, f"n={n}\nλGC={lambdagc:.3f}", transform=ax.transAxes,
            fontsize=9, verticalalignment="top")
    fig.tight_layout(); fig.savefig(output, dpi=dpi)
    print(f"QQ plot: {output} (λGC={lambdagc:.4f})")
    return output

# ---- Regional plot ----
def plot_regional(sumstats_file, locus, output, dpi=150):
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib not installed"); return
    df = pd.read_csv(sumstats_file, delim_whitespace=True)
    chr_col, pos_col, pval_col, *_ = detect_cols(df)
    parts = locus.replace("chr","").split(":")
    chrom = parts[0]
    if "-" in parts[1]: start, end = map(int, parts[1].split("-"))
    else: center = int(parts[1]); start, end = center - 500000, center + 500000
    mask = (df[chr_col].astype(str) == str(chrom)) & \
           (df[pos_col].astype(int) >= start) & (df[pos_col].astype(int) <= end)
    locus_df = df[mask]
    if len(locus_df) == 0:
        print(f"No SNPs in locus {locus}"); return
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(locus_df[pos_col].astype(int), -np.log10(locus_df[pval_col].astype(float).clip(lower=1e-300)),
               s=15, c="steelblue", alpha=0.7)
    ax.axhline(-np.log10(5e-8), color="red", linestyle="--", lw=0.5)
    ax.set_xlabel("Position (bp)"); ax.set_ylabel("-log10(P)")
    ax.set_title(f"Regional Plot {locus}")
    fig.tight_layout(); fig.savefig(output, dpi=dpi)
    print(f"Regional plot: {output} ({len(locus_df)} SNPs)")
    return output

# ---- Forest plot ----
def plot_forest(data_file, output, dpi=150):
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib not installed"); return
    df = pd.read_csv(data_file, sep="\t")
    label_col = next((c for c in ["Study","Gene","SNP","Label"] if c in df.columns), df.columns[0])
    beta_col = next((c for c in ["BETA","beta","Effect","OR"] if c in df.columns), None)
    se_col = next((c for c in ["SE","se","StdErr","CI_lower"] if c in df.columns), None)
    ci_lower = next((c for c in ["CI_lower","lower","Lower"] if c in df.columns), None)
    ci_upper = next((c for c in ["CI_upper","upper","Upper"] if c in df.columns), None)
    if not beta_col:
        print("ERROR: need BETA column"); return
    n = len(df)
    fig, ax = plt.subplots(figsize=(8, max(3, n * 0.4 + 1)))
    y_pos = range(n)
    betas = df[beta_col].astype(float).values
    if se_col and not ci_lower:
        lowers = betas - 1.96 * df[se_col].astype(float).values
        uppers = betas + 1.96 * df[se_col].astype(float).values
    elif ci_lower and ci_upper:
        lowers = df[ci_lower].astype(float).values
        uppers = df[ci_upper].astype(float).values
    else:
        lowers = betas - 0.1; uppers = betas + 0.1
    for i in range(n):
        ax.errorbar(betas[i], i, xerr=[[betas[i]-lowers[i]], [uppers[i]-betas[i]]],
                    fmt="o", color="steelblue", capsize=3, markersize=5)
    ax.axvline(0, color="black", linestyle="--", lw=0.5)
    ax.set_yticks(y_pos); ax.set_yticklabels(df[label_col].values, fontsize=9)
    ax.set_xlabel("Effect Size (BETA)"); ax.set_title("Forest Plot")
    ax.invert_yaxis()
    fig.tight_layout(); fig.savefig(output, dpi=dpi)
    print(f"Forest plot: {output} ({n} studies)")
    return output

# ---- Compare Manhattan ----
def plot_compare(sumstats1, sumstats2, output, dpi=150):
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("ERROR: matplotlib not installed"); return
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    for ax, sf, title in [(ax1, sumstats1, "Trait 1"), (ax2, sumstats2, "Trait 2")]:
        df = pd.read_csv(sf, delim_whitespace=True)
        chr_col, pos_col, pval_col, *_ = detect_cols(df)
        if not all([chr_col, pos_col, pval_col]): continue
        df = df.dropna(subset=[chr_col, pos_col, pval_col]).copy()
        df["CHR"] = df[chr_col].astype(str).str.replace("chr","").str.replace("X","23").astype(int)
        df = df[df["CHR"] <= 22].sort_values(["CHR", pos_col])
        df["neglogp"] = -np.log10(df[pval_col].astype(float).clip(lower=1e-300))
        df["cum"] = 0; offset = 0
        for c in sorted(df["CHR"].unique()):
            m = df["CHR"] == c
            df.loc[m, "cum"] = df.loc[m, pos_col].astype(int) + offset
            offset = df.loc[m, "cum"].max() + 5e6
        colors = ["#1f77b4", "#ff7f0e"] * 11
        for c in sorted(df["CHR"].unique()):
            m = df["CHR"] == c
            ax.scatter(df.loc[m, "cum"], df.loc[m, "neglogp"], s=1, c=colors[c-1], alpha=0.5)
        ax.set_ylabel("-log10(P)"); ax.set_title(title)
        ax.axhline(-np.log10(5e-8), color="red", linestyle="--", lw=0.5)
    ax2.set_xlabel("Chromosome")
    fig.tight_layout(); fig.savefig(output, dpi=dpi)
    print(f"Compare Manhattan: {output}")
    return output

# ---- Summary table ----
def report_summary(sumstats_file, output, top_n=20, threshold=5e-8):
    df = pd.read_csv(sumstats_file, delim_whitespace=True)
    pval_col = next((c for c in ["P","PVAL","PVALUE"] if c in df.columns), None)
    snp_col = next((c for c in ["SNP","rsID"] if c in df.columns), None)
    if not pval_col:
        print("ERROR: no p-value column"); return
    # Significant SNPs
    sig = df[df[pval_col].astype(float) < threshold].sort_values(pval_col)
    # Top N
    top = df.nsmallest(top_n, pval_col)
    result = pd.concat([sig.head(top_n), top[~top.index.isin(sig.head(top_n).index)]])
    result.to_csv(output, sep="\t", index=False)
    print(f"Summary: {output}")
    print(f"  Total SNPs: {len(df)}")
    print(f"  Significant (p<{threshold}): {len(sig)}")
    print(f"  Top {top_n}:")
    if snp_col:
        print(top[[snp_col, pval_col]].to_string(index=False))
    return output

# ---- Pipeline ----
def pipeline_full(args):
    os.makedirs(args.output, exist_ok=True)
    print("=== Manhattan Plot ===")
    plot_manhattan(args.sumstats, os.path.join(args.output, "manhattan.png"), args.threshold, args.highlight, args.dpi)
    print("\n=== QQ Plot ===")
    plot_qq(args.sumstats, os.path.join(args.output, "qq.png"), args.dpi)
    print("\n=== Summary Table ===")
    report_summary(args.sumstats, os.path.join(args.output, "summary.tsv"), args.top_n, args.threshold)
    print(f"\n=== Visualization Complete ===")
    print(f"  Output: {args.output}")

def main():
    parser = argparse.ArgumentParser(description="Population GWAS Visualization")
    sub = parser.add_subparsers(dest="module", required=True)
    p_pipe = sub.add_parser("pipeline"); p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full")
    p_full.add_argument("--sumstats", required=True); p_full.add_argument("--output", required=True)
    p_full.add_argument("--threshold", type=float, default=5e-8)
    p_full.add_argument("--dpi", type=int, default=150)
    p_full.add_argument("--highlight"); p_full.add_argument("--top-n", type=int, default=20)
    p_pl = sub.add_parser("plot"); p_pl_sub = p_pl.add_subparsers(dest="subcommand", required=True)
    p_man = p_pl_sub.add_parser("manhattan")
    p_man.add_argument("--sumstats", required=True); p_man.add_argument("--output", required=True)
    p_man.add_argument("--threshold", type=float, default=5e-8)
    p_man.add_argument("--highlight"); p_man.add_argument("--dpi", type=int, default=150)
    p_qq = p_pl_sub.add_parser("qq")
    p_qq.add_argument("--sumstats", required=True); p_qq.add_argument("--output", required=True)
    p_qq.add_argument("--dpi", type=int, default=150)
    p_reg = p_pl_sub.add_parser("regional")
    p_reg.add_argument("--sumstats", required=True); p_reg.add_argument("--locus", required=True)
    p_reg.add_argument("--output", required=True); p_reg.add_argument("--dpi", type=int, default=150)
    p_for = p_pl_sub.add_parser("forest")
    p_for.add_argument("--data", required=True); p_for.add_argument("--output", required=True)
    p_for.add_argument("--dpi", type=int, default=150)
    p_cmp = p_pl_sub.add_parser("compare")
    p_cmp.add_argument("--sumstats1", required=True); p_cmp.add_argument("--sumstats2", required=True)
    p_cmp.add_argument("--output", required=True); p_cmp.add_argument("--dpi", type=int, default=150)
    p_rep = sub.add_parser("report"); p_rep_sub = p_rep.add_subparsers(dest="subcommand", required=True)
    p_sum = p_rep_sub.add_parser("summary")
    p_sum.add_argument("--sumstats", required=True); p_sum.add_argument("--output", required=True)
    p_sum.add_argument("--top-n", type=int, default=20); p_sum.add_argument("--threshold", type=float, default=5e-8)
    args = parser.parse_args()
    if args.module == "pipeline" and args.subcommand == "full": pipeline_full(args)
    elif args.module == "plot":
        if args.subcommand == "manhattan": plot_manhattan(args.sumstats, args.output, args.threshold, args.highlight, args.dpi)
        elif args.subcommand == "qq": plot_qq(args.sumstats, args.output, args.dpi)
        elif args.subcommand == "regional": plot_regional(args.sumstats, args.locus, args.output, args.dpi)
        elif args.subcommand == "forest": plot_forest(args.data, args.output, args.dpi)
        elif args.subcommand == "compare": plot_compare(args.sumstats1, args.sumstats2, args.output, args.dpi)
    elif args.module == "report" and args.subcommand == "summary":
        report_summary(args.sumstats, args.output, args.top_n, args.threshold)

if __name__ == "__main__":
    main()
