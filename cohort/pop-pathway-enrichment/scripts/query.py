#!/usr/bin/env python3
"""
Population Pathway Enrichment — query.py
=========================================
基因水平关联 + 通路富集 + 组织特异性。
MAGMA / Python 聚合。

依赖: pandas, numpy
可选: MAGMA (conda install -c bioconda magma)
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

MAGMA_BIN = shutil.which("magma") or shutil.which("MAGMA")


# ---- Gene-based test ----
def gene_test(sumstats_file, output_dir, genome="GRCh38", gene_window=35000, n=None):
    """Gene-based association test using MAGMA or Python fallback."""
    os.makedirs(output_dir, exist_ok=True)
    if MAGMA_BIN:
        # MAGMA workflow: annotate → gene-level analysis
        annot_file = os.path.join(output_dir, "gene_annot")
        result_file = os.path.join(output_dir, "gene_results")
        # Step 1: Annotation
        cmd1 = [MAGMA_BIN, "--annotate",
                "--snp-loc", sumstats_file,
                "--gene-loc", f"NCBI{genome}.genes.loc",
                "--out", annot_file]
        print("MAGMA annotation...")
        try:
            r1 = subprocess.run(cmd1, capture_output=True, text=True, timeout=3600)
            if r1.returncode != 0:
                print(f"MAGMA annotate failed: {r1.stderr[:500]}")
                return gene_test_python(sumstats_file, output_dir, gene_window)
        except subprocess.TimeoutExpired:
            print("MAGMA annotate timed out")
            return gene_test_python(sumstats_file, output_dir, gene_window)
        # Step 2: Gene-level analysis
        cmd2 = [MAGMA_BIN, "--gene-results", annot_file + ".genes",
                "--gene-annot", annot_file + ".genes.annot",
                "--out", result_file]
        if n:
            cmd2 += ["--N", str(n)]
        print("MAGMA gene analysis...")
        try:
            r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=3600)
            if r2.returncode == 0:
                out_file = result_file + ".genes.out"
                if os.path.isfile(out_file):
                    df = pd.read_csv(out_file, delim_whitespace=True)
                    print(f"MAGMA gene results: {out_file} ({len(df)} genes)")
                    return out_file
        except subprocess.TimeoutExpired:
            print("MAGMA gene analysis timed out")
    print("MAGMA not found. Using Python gene aggregation...")
    return gene_test_python(sumstats_file, output_dir, gene_window)


def gene_test_python(sumstats_file, output_dir, gene_window=35000):
    """Python fallback: aggregate SNP p-values to gene-level."""
    df = pd.read_csv(sumstats_file, delim_whitespace=True)
    chr_col = next((c for c in ["CHR", "CHROM"] if c in df.columns), None)
    pos_col = next((c for c in ["BP", "POS"] if c in df.columns), None)
    pval_col = next((c for c in ["P", "PVAL"] if c in df.columns), None)
    snp_col = next((c for c in ["SNP", "rsID"] if c in df.columns), None)
    if not all([chr_col, pos_col, pval_col]):
        print(f"ERROR: need CHR, BP, P columns. Found: {list(df.columns)}")
        return None
    # Try to load gene annotation
    gene_file = None
    for path in ["/public/database/refseq/NCBI_GRCh38.genes.loc",
                 "/public/database/refseq/NCBI_GRCh37.genes.loc",
                 os.path.join(output_dir, "genes.loc")]:
        if os.path.isfile(path):
            gene_file = path
            break
    if not gene_file:
        # Create minimal gene annotation from known gene positions
        print("No gene annotation file found. Using simplified aggregation by genomic bins.")
        # Bin SNPs into 35kb windows and treat as "genes"
        df = df.sort_values([chr_col, pos_col])
        df["bin"] = df[pos_col] // gene_window
        gene_results = df.groupby([chr_col, "bin"]).agg(
            n_snps=(pval_col, "count"),
            min_p=(pval_col, "min"),
            mean_chi2=(pval_col, lambda x: np.mean(-2 * np.log(x.astype(float).clip(lower=1e-300))))
        ).reset_index()
        gene_results["gene_id"] = gene_results[chr_col].astype(str) + ":" + gene_results["bin"].astype(str)
        # Fisher's method for combining p-values
        from scipy.stats import chi2 as chi2_dist
        gene_results["combined_p"] = gene_results.apply(
            lambda r: chi2_dist.sf(-2 * np.sum(np.log(
                df[(df[chr_col] == r[chr_col]) & (df["bin"] == r["bin"])][pval_col].astype(float).clip(lower=1e-300)
            )), 2 * r["n_snps"]), axis=1)
        result_file = os.path.join(output_dir, "gene_results.txt")
        gene_results.to_csv(result_file, sep="\t", index=False)
        print(f"Gene aggregation (bins): {result_file} ({len(gene_results)} bins)")
        return result_file
    # With gene annotation
    genes = pd.read_csv(gene_file, delim_whitespace=True, header=None,
                        names=["CHR", "START", "END", "GENE", "STRAND"])
    gene_pvals = []
    for _, gene in genes.iterrows():
        mask = (df[chr_col].astype(int) == int(gene["CHR"])) & \
               (df[pos_col].astype(int) >= int(gene["START"]) - gene_window) & \
               (df[pos_col].astype(int) <= int(gene["END"]) + gene_window)
        gene_snps = df[mask]
        if len(gene_snps) == 0:
            continue
        # Fisher's method
        chi2_stat = -2 * np.sum(np.log(gene_snps[pval_col].astype(float).clip(lower=1e-300)))
        from scipy.stats import chi2 as chi2_dist
        combined_p = chi2_dist.sf(chi2_stat, 2 * len(gene_snps))
        gene_pvals.append({"GENE": gene["GENE"], "CHR": gene["CHR"],
                          "START": gene["START"], "END": gene["END"],
                          "n_snps": len(gene_snps), "combined_p": combined_p})
    result_df = pd.DataFrame(gene_pvals).sort_values("combined_p")
    result_file = os.path.join(output_dir, "gene_results.txt")
    result_df.to_csv(result_file, sep="\t", index=False)
    print(f"Gene results: {result_file} ({len(result_df)} genes)")
    print(f"Top 10 genes:")
    print(result_df.head(10)[["GENE", "n_snps", "combined_p"]].to_string(index=False))
    return result_file


# ---- Pathway enrichment ----
def pathway_enrich(gene_results_file, output_dir, pval_threshold=0.05):
    """Pathway enrichment from gene-level results."""
    os.makedirs(output_dir, exist_ok=True)
    gene_df = pd.read_csv(gene_results_file, sep="\t")
    pval_col = next((c for c in ["combined_p", "P", "PVAL"] if c in gene_df.columns), None)
    gene_col = next((c for c in ["GENE", "GENE_NAME", "SYMBOL"] if c in gene_df.columns), None)
    if not pval_col or not gene_col:
        print(f"ERROR: need GENE and p-value columns. Found: {list(gene_df.columns)}")
        return None
    # Define significant genes
    sig_genes = set(gene_df[gene_df[pval_col].astype(float) < pval_threshold][gene_col])
    all_genes = set(gene_df[gene_col])
    print(f"Significant genes: {len(sig_genes)} / {len(all_genes)} (p < {pval_threshold})")
    # Try to load pathway database
    pathway_files = []
    for path in ["/public/database/kegg/kegg_pathways.tsv",
                 "/public/database/go/go_terms.tsv",
                 os.path.join(output_dir, "pathways.tsv")]:
        if os.path.isfile(path):
            pathway_files.append(path)
    if not pathway_files:
        print("No pathway database found. Using built-in example pathways.")
        # Built-in example: common pathways
        example_pathways = {
            "Immune_response": ["HLA-A", "HLA-B", "HLA-C", "CD4", "CD8A", "IL2", "IL4", "IL10", "FOXP3", "TNF"],
            "Lipid_metabolism": ["APOE", "APOB", "LDLR", "PCSK9", "HMGCR", "LPL", "CETP", "ABCA1", "LDRAP1"],
            "Insulin_signaling": ["INS", "INSR", "IRS1", "IRS2", "AKT1", "AKT2", "PTEN", "GSK3B", "SLC2A4"],
            "Cell_cycle": ["TP53", "CDKN1A", "CDKN2A", "RB1", "CCND1", "CDK4", "CDK6", "E2F1", "MDM2"],
        }
        results = []
        for pathway_name, pathway_genes in example_pathways.items():
            overlap = sig_genes & set(pathway_genes)
            all_overlap = all_genes & set(pathway_genes)
            if len(all_overlap) == 0:
                continue
            from scipy.stats import fisher_exact
            table = [[len(overlap), len(sig_genes) - len(overlap)],
                     [len(all_overlap) - len(overlap), len(all_genes) - len(sig_genes) - len(all_overlap) + len(overlap)]]
            or_val, p_val = fisher_exact(table, alternative="greater")
            results.append({"Pathway": pathway_name, "n_overlap": len(overlap),
                           "n_pathway": len(all_overlap), "n_sig": len(sig_genes),
                           "odds_ratio": or_val, "p_value": p_val,
                           "genes": ",".join(sorted(overlap))})
        result_df = pd.DataFrame(results).sort_values("p_value")
        result_file = os.path.join(output_dir, "pathway_enrichment.txt")
        result_df.to_csv(result_file, sep="\t", index=False)
        print(f"Pathway enrichment: {result_file}")
        if len(result_df) > 0:
            print(result_df[["Pathway", "n_overlap", "odds_ratio", "p_value"]].to_string(index=False))
        return result_file
    # With pathway database
    for pf in pathway_files:
        print(f"Using pathway database: {pf}")
        # Implementation would parse pathway file and run Fisher's exact test
        pass
    return None


# ---- Tissue enrichment ----
def tissue_enrich(gene_results_file, expression_file, output_dir):
    """Tissue specificity enrichment."""
    os.makedirs(output_dir, exist_ok=True)
    print("Tissue enrichment requires expression data (e.g., GTEx).")
    print("Running simplified tissue enrichment...")
    gene_df = pd.read_csv(gene_results_file, sep="\t")
    pval_col = next((c for c in ["combined_p", "P"] if c in gene_df.columns), None)
    gene_col = next((c for c in ["GENE", "SYMBOL"] if c in gene_df.columns), None)
    if not pval_col:
        return None
    sig_genes = set(gene_df[gene_df[pval_col] < 0.05][gene_col])
    if expression_file and os.path.isfile(expression_file):
        expr = pd.read_csv(expression_file, sep="\t", index_col=0)
        # For each tissue column, test enrichment
        results = []
        for tissue in expr.columns:
            tissue_genes = set(expr[expr[tissue] > expr[tissue].quantile(0.75)].index)
            overlap = sig_genes & tissue_genes
            if len(overlap) < 3:
                continue
            from scipy.stats import fisher_exact
            table = [[len(overlap), len(sig_genes) - len(overlap)],
                     [len(tissue_genes) - len(overlap),
                      len(gene_df) - len(sig_genes) - len(tissue_genes) + len(overlap)]]
            or_val, p_val = fisher_exact(table, alternative="greater")
            results.append({"Tissue": tissue, "n_overlap": len(overlap),
                           "odds_ratio": or_val, "p_value": p_val})
        result_df = pd.DataFrame(results).sort_values("p_value")
        result_file = os.path.join(output_dir, "tissue_enrichment.txt")
        result_df.to_csv(result_file, sep="\t", index=False)
        print(f"Tissue enrichment: {result_file}")
        return result_file
    print("No expression file provided. Skipping tissue enrichment.")
    return None


# ---- Pipeline ----
def pipeline_full(args):
    """Full pathway enrichment pipeline."""
    os.makedirs(args.output, exist_ok=True)
    print("=== Step 1: Gene-Based Test ===")
    gene_file = gene_test(args.sumstats, os.path.join(args.output, "gene_test"),
                          args.genome, args.gene_window)
    if not gene_file:
        return
    print("\n=== Step 2: Pathway Enrichment ===")
    pathway_enrich(gene_file, os.path.join(args.output, "pathway"))
    print(f"\n=== Pathway Enrichment Complete ===")
    print(f"  Results: {args.output}")


def main():
    parser = argparse.ArgumentParser(description="Population Pathway Enrichment")
    sub = parser.add_subparsers(dest="module", required=True)

    # pipeline
    p_pipe = sub.add_parser("pipeline")
    p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full")
    p_full.add_argument("--sumstats", required=True)
    p_full.add_argument("--output", required=True)
    p_full.add_argument("--genome", default="GRCh38", choices=["GRCh37", "GRCh38"])
    p_full.add_argument("--gene-window", type=int, default=35000)
    p_full.add_argument("--n", type=int)

    # gene
    p_g = sub.add_parser("gene")
    p_g_sub = p_g.add_subparsers(dest="subcommand", required=True)
    p_gt = p_g_sub.add_parser("test")
    p_gt.add_argument("--sumstats", required=True)
    p_gt.add_argument("--output", required=True)
    p_gt.add_argument("--genome", default="GRCh38", choices=["GRCh37", "GRCh38"])
    p_gt.add_argument("--gene-window", type=int, default=35000)
    p_gt.add_argument("--n", type=int)

    # pathway
    p_p = sub.add_parser("pathway")
    p_p_sub = p_p.add_subparsers(dest="subcommand", required=True)
    p_pe = p_p_sub.add_parser("enrich")
    p_pe.add_argument("--gene-results", required=True)
    p_pe.add_argument("--output", required=True)
    p_pe.add_argument("--pval-threshold", type=float, default=0.05)

    # tissue
    p_t = sub.add_parser("tissue")
    p_t_sub = p_t.add_subparsers(dest="subcommand", required=True)
    p_te = p_t_sub.add_parser("enrich")
    p_te.add_argument("--gene-results", required=True)
    p_te.add_argument("--expression", required=True, help="Expression matrix (GTEx)")
    p_te.add_argument("--output", required=True)

    args = parser.parse_args()

    if args.module == "pipeline" and args.subcommand == "full":
        pipeline_full(args)
    elif args.module == "gene" and args.subcommand == "test":
        gene_test(args.sumstats, args.output, args.genome, args.gene_window, args.n)
    elif args.module == "pathway" and args.subcommand == "enrich":
        pathway_enrich(args.gene_results, args.output, args.pval_threshold)
    elif args.module == "tissue" and args.subcommand == "enrich":
        tissue_enrich(args.gene_results, args.expression, args.output)


if __name__ == "__main__":
    main()
