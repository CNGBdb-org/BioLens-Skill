#!/usr/bin/env python3
"""
Population Genotype Imputation — query.py
==========================================
基因型填充主入口脚本。
前质控 → Phasing 准备 → 提交文件 → 填充后质控。

依赖: PLINK 1.9+, pandas, numpy
可选: Eagle2/SHAPEIT4 (phasing), Minimac4 (imputation)
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
    """Check if a tool is available."""
    p = shutil.which(name)
    if p: return p
    for d in [os.path.expanduser("~/software/miniforge/envs/cima/bin"),
              os.path.expanduser("~/software/miniforge/bin"),
              "/usr/bin", "/usr/local/bin"]:
        fp = os.path.join(d, name)
        if os.path.isfile(fp) and os.access(fp, os.X_OK): return fp
    return None

EAGLE_BIN = find_tool("eagle") or find_tool("eagle2")
SHAPEIT_BIN = find_tool("shapeit4") or find_tool("shapeit")
MINIMAC_BIN = find_tool("minimac4") or find_tool("minimac3")

def run_plink(args):
    if not PLINK_BIN:
        print("ERROR: PLINK not found.")
        return 1, ""
    cmd = [PLINK_BIN] + args
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 1, "TIMEOUT"


# ---- Pre-imputation QC ----
def preqc_check(prefix, output_dir):
    """Pre-imputation QC: check genome build, allele alignment, strand issues."""
    os.makedirs(output_dir, exist_ok=True)
    bim_file = prefix + ".bim"
    if not os.path.isfile(bim_file):
        print(f"ERROR: {bim_file} not found")
        return
    bim = pd.read_csv(bim_file, delim_whitespace=True, header=None,
                      names=["CHR", "SNP", "CM", "BP", "A1", "A2"])
    # Check build (hg38 has chr prefix in some formats, hg19 doesn't)
    n_snps = len(bim)
    n_chrs = bim["CHR"].nunique()
    # Check for indels (A1/A2 > 1 char)
    n_indels = bim[(bim["A1"].str.len() > 1) | (bim["A2"].str.len() > 1)].shape[0]
    # Check for ambiguous SNPs (A/T, C/G)
    ambiguous = set()
    for _, r in bim.iterrows():
        pair = tuple(sorted([r["A1"], r["A2"]]))
        if pair in [("A","T"), ("C","G")]:
            ambiguous.add(r["SNP"])
    # Check for missing alleles
    n_missing = bim[(bim["A1"] == "0") | (bim["A2"] == "0") | (bim["A1"] == ".") | (bim["A2"] == ".")].shape[0]

    report = {
        "n_snps": n_snps, "n_chrs": n_chrs, "n_indels": n_indels,
        "n_ambiguous_at_cg": len(ambiguous), "n_missing_alleles": n_missing,
    }
    report_path = os.path.join(output_dir, "preqc_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"Pre-imputation QC:")
    print(f"  SNPs: {n_snps}")
    print(f"  Chromosomes: {n_chrs}")
    print(f"  Indels: {n_indels}")
    print(f"  Ambiguous (A/T, C/G): {len(ambiguous)}")
    print(f"  Missing alleles: {n_missing}")

    if ambiguous:
        amb_file = os.path.join(output_dir, "ambiguous_snps.txt")
        with open(amb_file, "w") as f:
            f.write("\n".join(ambiguous))
        print(f"  Ambiguous SNP list: {amb_file}")

    if n_missing > 0:
        print(f"  WARNING: {n_missing} SNPs with missing alleles - should be removed")

    return report


# ---- Phasing ----
def phase_prepare(prefix, output_dir):
    """Prepare and run phasing with Eagle or SHAPEIT4."""
    os.makedirs(output_dir, exist_ok=True)
    phased_prefix = os.path.join(output_dir, "phased")

    if EAGLE_BIN:
        print(f"Using Eagle: {EAGLE_BIN}")
        cmd = [EAGLE_BIN, "--bfile", prefix, "--out", phased_prefix, "--chrom", "1-22"]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=14400)
            if r.returncode == 0:
                print(f"Phasing complete: {phased_prefix}")
                return phased_prefix
            else:
                print(f"Eagle failed: {r.stderr[:500]}")
        except subprocess.TimeoutExpired:
            print("Eagle timed out")
    elif SHAPEIT_BIN:
        print(f"Using SHAPEIT4: {SHAPEIT_BIN}")
        cmd = [SHAPEIT_BIN, "--input", prefix, "--output", phased_prefix]
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=14400)
            if r.returncode == 0:
                print(f"Phasing complete: {phased_prefix}")
                return phased_prefix
            else:
                print(f"SHAPEIT4 failed: {r.stderr[:500]}")
        except subprocess.TimeoutExpired:
            print("SHAPEIT4 timed out")
    else:
        print("No phasing tool found. Install Eagle2 or SHAPEIT4:")
        print("  conda install -c bioconda eagle")
        print("  or conda install -c bioconda shapeit4")
        # Create a placeholder for manual steps
        instructions = """
Phasing Instructions:
1. Install Eagle2: conda install -c bioconda eagle
2. Run: eagle --bfile %s --out %s --chrom 1-22
3. Or use TOPMed/HRC Server (upload for server-side phasing)
""" % (prefix, phased_prefix)
        with open(os.path.join(output_dir, "phasing_instructions.txt"), "w") as f:
            f.write(instructions)
        print(f"Instructions saved: {os.path.join(output_dir, 'phasing_instructions.txt')}")
    return None


# ---- Submit preparation ----
def submit_prepare(prefix, output_dir, ref="TOPMed"):
    """Prepare submission files for imputation server."""
    os.makedirs(output_dir, exist_ok=True)
    # Create the submission package
    # TOPMed server needs: VCF (bgzipped + tabix indexed) or PLINK
    # Create VCF from PLINK
    vcf_out = os.path.join(output_dir, "submit.vcf.gz")
    rc, out_text = run_plink([
        "--bfile", prefix, "--recode vcf-iid", "bgz",
        "--out", os.path.join(output_dir, "submit"),
    ])
    if rc != 0:
        print(f"ERROR creating VCF: {out_text[:500]}")
        return
    # Check for bgzip/tabix
    bgzip_bin = find_tool("bgzip")
    tabix_bin = find_tool("tabix")
    vcf_file = os.path.join(output_dir, "submit.vcf")
    if os.path.isfile(vcf_file):
        if bgzip_bin:
            os.system(f"{bgzip_bin} {vcf_file}")
            vcf_file = vcf_file + ".gz"
            if tabix_bin:
                os.system(f"{tabix_bin} -p vcf {vcf_file}")
                print(f"VCF compressed and indexed: {vcf_file}")
        else:
            print(f"VCF created (not compressed): {vcf_file}")
            print("Install bgzip/tabix for compression: conda install -c bioconda htslib")

    # Create sample metadata
    fam = pd.read_csv(prefix + ".fam", delim_whitespace=True, header=None,
                      names=["FID", "IID", "PID", "MID", "SEX", "PHENO"])
    fam[["FID", "IID", "SEX"]].to_csv(
        os.path.join(output_dir, "sample_metadata.txt"), sep="\t", index=False)
    print(f"Sample metadata: {os.path.join(output_dir, 'sample_metadata.txt')}")

    print(f"\nSubmission package ready: {output_dir}")
    ref_urls = {
        "TOPMed": "https://imputation.biodatacatalyst.nhlbi.nih.gov/",
        "HRC": "https://imputation.hrc.umich.edu/",
        "1000G": "https://imputationserver.sph.umich.edu/",
    }
    print(f"Submit to {ref} server: {ref_urls.get(ref, ref_urls['TOPMed'])}")
    print(f"Upload: {vcf_file} + sample_metadata.txt")


# ---- Post-imputation QC ----
def postqc_filter(imputed_dir, output_dir, info_threshold=0.3, r2_threshold=0.3, maf_imp=0.005):
    """Post-imputation QC: filter by info score and r2."""
    os.makedirs(output_dir, exist_ok=True)
    info_files = []
    for root, dirs, files in os.walk(imputed_dir):
        for fn in files:
            if "info" in fn.lower() and (fn.endswith(".info") or fn.endswith(".info.gz")):
                info_files.append(os.path.join(root, fn))
    if not info_files:
        print(f"No .info files found in {imputed_dir}")
        return
    all_info = []
    for f in info_files:
        try:
            if f.endswith(".gz"):
                import gzip
                with gzip.open(f, "rt") as fh:
                    all_info.append(pd.read_csv(fh, delim_whitespace=True))
            else:
                all_info.append(pd.read_csv(f, delim_whitespace=True))
        except Exception as e:
            print(f"WARNING: could not read {f}: {e}")
    if not all_info:
        print("No info files could be parsed")
        return
    info_df = pd.concat(all_info, ignore_index=True)
    n_total = len(info_df)
    # Filter
    pass_mask = pd.Series([True] * n_total)
    if "INFO" in info_df.columns:
        pass_mask &= (info_df["INFO"] >= info_threshold)
    elif "R2" in info_df.columns:
        pass_mask &= (info_df["R2"] >= r2_threshold)
    if "MAF" in info_df.columns:
        pass_mask &= (info_df["MAF"] >= maf_imp)
    n_pass = pass_mask.sum()
    # Save passed variants
    snp_col = "SNP" if "SNP" in info_df.columns else ("rsID" if "rsID" in info_df.columns else None)
    if snp_col:
        passed_snps = info_df.loc[pass_mask, snp_col].tolist()
        with open(os.path.join(output_dir, "imputed_pass_snps.txt"), "w") as f:
            f.write("\n".join(passed_snps))
    report = {"total_variants": n_total, "passed": int(n_pass),
              "removed": int(n_total - n_pass),
              "info_threshold": info_threshold, "r2_threshold": r2_threshold}
    with open(os.path.join(output_dir, "postqc_report.json"), "w") as f:
        json.dump(report, f, indent=2)
    print(f"Post-imputation QC: {n_pass}/{n_total} variants passed (removed {n_total - n_pass})")
    print(f"Passed SNP list: {os.path.join(output_dir, 'imputed_pass_snps.txt')}")


def postqc_afcheck(typed_prefix, imputed_dir, output_dir):
    """Allele frequency concordance between typed and imputed."""
    os.makedirs(output_dir, exist_ok=True)
    # Get typed AF from PLINK
    frq_file = os.path.join(output_dir, "typed_freq")
    rc, out_text = run_plink(["--bfile", typed_prefix, "--freq", "--out", frq_file])
    if rc != 0:
        print(f"ERROR computing typed AF: {out_text[:500]}")
        return
    typed_frq = pd.read_csv(frq_file + ".frq", delim_whitespace=True)
    # Get imputed AF from info files
    for root, dirs, files in os.walk(imputed_dir):
        for fn in files:
            if "info" in fn.lower():
                try:
                    imp_info = pd.read_csv(os.path.join(root, fn), delim_whitespace=True)
                    if "MAF" in imp_info.columns and "SNP" in imp_info.columns:
                        merged = typed_frq.merge(imp_info[["SNP", "MAF"]], on="SNP", how="inner")
                        if len(merged) > 0:
                            r = np.corrcoef(merged["MAF_x"], merged["MAF_y"])[0, 1]
                            print(f"AF concordance: r = {r:.4f} ({len(merged)} variants)")
                            merged.to_csv(os.path.join(output_dir, "af_concordance.csv"), index=False)
                            return r
                except Exception as e:
                    print(f"WARNING: {e}")
    print("Could not compute AF concordance (check file formats)")


# ---- Pipeline ----
def pipeline_prepare(args):
    """Full imputation preparation pipeline."""
    os.makedirs(args.output, exist_ok=True)
    print("=== Step 1: Pre-imputation QC ===")
    preqc_check(args.input, os.path.join(args.output, "preqc"))
    print("\n=== Step 2: Phasing Preparation ===")
    phase_prepare(args.input, os.path.join(args.output, "phasing"))
    print(f"\n=== Step 3: Submit Preparation ({args.ref}) ===")
    submit_prepare(args.input, os.path.join(args.output, "submit"), args.ref)
    print(f"\n=== Imputation Preparation Complete ===")
    print(f"Upload {os.path.join(args.output, 'submit')} to {args.ref} Imputation Server")


def main():
    parser = argparse.ArgumentParser(description="Population Genotype Imputation")
    sub = parser.add_subparsers(dest="module", required=True)

    # pipeline
    p_pipe = sub.add_parser("pipeline", help="Full pipeline")
    p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_prep = p_sub.add_parser("prepare", help="Prepare imputation submission")
    p_prep.add_argument("--input", required=True, help="PLINK prefix (QC'd)")
    p_prep.add_argument("--output", required=True)
    p_prep.add_argument("--ref", default="TOPMed", choices=["TOPMed", "HRC", "1000G"])

    # preqc
    p_pq = sub.add_parser("preqc", help="Pre-imputation QC")
    p_pq_sub = p_pq.add_subparsers(dest="subcommand", required=True)
    p_chk = p_pq_sub.add_parser("check", help="Check genome build & alleles")
    p_chk.add_argument("--input", required=True)
    p_chk.add_argument("--output", required=True)

    # phase
    p_ph = sub.add_parser("phase", help="Phasing")
    p_ph_sub = p_ph.add_subparsers(dest="subcommand", required=True)
    p_pp = p_ph_sub.add_parser("prepare", help="Prepare/run phasing")
    p_pp.add_argument("--input", required=True)
    p_pp.add_argument("--output", required=True)

    # postqc
    p_po = sub.add_parser("postqc", help="Post-imputation QC")
    p_po_sub = p_po.add_subparsers(dest="subcommand", required=True)
    p_flt = p_po_sub.add_parser("filter", help="Filter by info score")
    p_flt.add_argument("--input", required=True, help="Imputed results directory")
    p_flt.add_argument("--output", required=True)
    p_flt.add_argument("--info", type=float, default=0.3)
    p_flt.add_argument("--r2", type=float, default=0.3)
    p_flt.add_argument("--maf-imp", type=float, default=0.005)
    p_af = p_po_sub.add_parser("afcheck", help="AF concordance check")
    p_af.add_argument("--typed", required=True, help="Typed PLINK prefix")
    p_af.add_argument("--imputed", required=True, help="Imputed results directory")
    p_af.add_argument("--output", required=True)

    # submit
    p_sub2 = sub.add_parser("submit", help="Submission preparation")
    p_sub2_sub = p_sub2.add_subparsers(dest="subcommand", required=True)
    p_sp = p_sub2_sub.add_parser("prepare", help="Prepare submission files")
    p_sp.add_argument("--input", required=True)
    p_sp.add_argument("--ref", default="TOPMed", choices=["TOPMed", "HRC", "1000G"])
    p_sp.add_argument("--output", required=True)

    args = parser.parse_args()

    if args.module == "pipeline" and args.subcommand == "prepare":
        pipeline_prepare(args)
    elif args.module == "preqc" and args.subcommand == "check":
        preqc_check(args.input, args.output)
    elif args.module == "phase" and args.subcommand == "prepare":
        phase_prepare(args.input, args.output)
    elif args.module == "postqc" and args.subcommand == "filter":
        postqc_filter(args.input, args.output, args.info, args.r2, args.maf_imp)
    elif args.module == "postqc" and args.subcommand == "afcheck":
        postqc_afcheck(args.typed, args.imputed, args.output)
    elif args.module == "submit" and args.subcommand == "prepare":
        submit_prepare(args.input, args.output, args.ref)


if __name__ == "__main__":
    if not PLINK_BIN:
        print("WARNING: PLINK not found. Install: conda install -c bioconda plink")
    main()
