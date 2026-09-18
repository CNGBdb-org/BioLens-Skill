#!/usr/bin/env python3
"""
Population Genotype QC — query.py
=================================
群体基因型质控主入口脚本。
支持 VCF / PLINK 输入，自动检测 PLINK 路径。

模块:
  pipeline   全流程 QC（sample + variant）
  sample     样本水平 QC（missingness / sexcheck / het / relatedness）
  variant    变异水平 QC（missingness / maf / hwe）
  convert    格式转换（vcf2plink）
  report     QC 报告汇总

依赖: PLINK 1.9+, pysam, pandas, numpy, scipy
"""
import argparse
import os
import sys
import shutil
import subprocess
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

# ---- PLINK detection ----
def find_plink():
    """Auto-detect plink2 or plink1.9 binary path."""
    for name in ["plink2", "plink"]:
        p = shutil.which(name)
        if p:
            return p, name
        for d in [
            os.path.expanduser("~/software/miniforge/envs/cima/bin"),
            os.path.expanduser("~/software/miniforge/bin"),
            "/usr/bin", "/usr/local/bin",
        ]:
                fp = os.path.join(d, name)
                if os.path.isfile(fp) and os.access(fp, os.X_OK):
                    return fp, name
    return None, None


PLINK_BIN, PLINK_NAME = find_plink()


def run_plink(args, log_file=None):
    """Run PLINK command, return (returncode, stdout)."""
    if not PLINK_BIN:
        return 1, "ERROR: PLINK not found. Install: conda install -c bioconda plink"
    cmd = [PLINK_BIN] + args
    if log_file:
        cmd += ["--out", log_file]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        return r.returncode, r.stdout + r.stderr
    except subprocess.TimeoutExpired:
        return 1, "ERROR: PLINK timed out after 3600s"


def detect_input_type(input_path):
    """Detect if input is VCF or PLINK prefix."""
    p = str(input_path)
    if p.endswith(".vcf") or p.endswith(".vcf.gz"):
        return "vcf"
    if os.path.isfile(p + ".bed"):
        return "plink"
    if os.path.isfile(p):
        return "vcf" if p.endswith(".vcf") else "plink"
    return "plink"


def vcf_to_plink(vcf_path, output_prefix, chr_x=False):
    """Convert VCF to PLINK bed/bim/fam."""
    args = ["--vcf", vcf_path, "--make-bed"]
    if chr_x:
        args += ["--split-chr"]
    args += ["--out", output_prefix]
    rc, out = run_plink(args)
    if rc != 0:
        print(f"ERROR converting VCF: {out}")
        return False
    print(f"VCF converted to PLINK: {output_prefix}.bed/.bim/.fam")
    return True


# ---- Sample QC ----
def sample_missingness(prefix, output_dir, threshold=0.02):
    """Sample missingness filter."""
    out = os.path.join(output_dir, "sample_missing")
    rc, out_text = run_plink([
        "--bfile", prefix, "--missing", "--out", out
    ])
    if rc != 0:
        print(f"ERROR: {out_text}")
        return None, None
    imiss = pd.read_csv(out + ".imiss", delim_whitespace=True)
    imiss["miss_rate"] = imiss["F_MISS"].astype(float)
    n_fail = (imiss["miss_rate"] > threshold).sum()
    pass_samples = imiss[imiss["miss_rate"] <= threshold]["IID"].tolist()
    fail_samples = imiss[imiss["miss_rate"] > threshold]["IID"].tolist()
    print(f"Sample missingness: {len(pass_samples)} passed, {n_fail} failed (>{threshold})")
    return pass_samples, fail_samples


def sex_check(prefix, output_dir, f_female=0.2, f_male=0.8):
    """Sex check based on X chromosome heterozygosity."""
    out = os.path.join(output_dir, "sexcheck")
    rc, out_text = run_plink([
        "--bfile", prefix, "--check-sex", "--out", out
    ])
    if rc != 0:
        print(f"ERROR: {out_text}")
        return None
    df = pd.read_csv(out + ".sexcheck", delim_whitespace=True)
    # SNPSEX: 1=male, 2=female
    df["status"] = df.apply(
        lambda r: "ok" if (
            (r["SNPSEX"] == 1 and r["F"] >= f_male) or
            (r["SNPSEX"] == 2 and r["F"] <= f_female)
        ) else "mismatch", axis=1
    )
    n_mismatch = (df["status"] == "mismatch").sum()
    print(f"Sex check: {len(df)} samples, {n_mismatch} sex mismatches")
    df.to_csv(os.path.join(output_dir, "sexcheck_report.csv"), index=False)
    return df


def heterozygosity(prefix, output_dir, threshold_sd=3):
    """Detect heterozygosity outliers."""
    # Step 1: calculate per-sample het
    out_het = os.path.join(output_dir, "het")
    rc, out_text = run_plink([
        "--bfile", prefix, "--het", "--out", out_het
    ])
    if rc != 0:
        print(f"ERROR: {out_text}")
        return None
    het = pd.read_csv(out_het + ".het", delim_whitespace=True)
    het["het_rate"] = het["O(HOM)"] / (het["O(HOM)"] + het["O(HET)"])
    mean_het = het["het_rate"].mean()
    std_het = het["het_rate"].std()
    het["z_score"] = (het["het_rate"] - mean_het) / std_het
    het["status"] = het["z_score"].apply(
        lambda z: "outlier" if abs(z) > threshold_sd else "ok"
    )
    n_outlier = (het["status"] == "outlier").sum()
    print(f"Heterozygosity: mean={mean_het:.4f}, sd={std_het:.4f}, {n_outlier} outliers (|z|>{threshold_sd})")
    het.to_csv(os.path.join(output_dir, "het_report.csv"), index=False)
    return het


def relatedness(prefix, output_dir, threshold=0.0884):
    """Detect related individuals (IBD / kinship)."""
    out_genome = os.path.join(output_dir, "ibd")
    rc, out_text = run_plink([
        "--bfile", prefix, "--genome", "--min", str(threshold),
        "--out", out_genome
    ])
    if rc != 0:
        print(f"ERROR: {out_text}")
        return None
    genome_file = out_genome + ".genome"
    if not os.path.isfile(genome_file):
        print("No related pairs found above threshold")
        return pd.DataFrame()
    rel = pd.read_csv(genome_file, delim_whitespace=True)
    print(f"Relatedness: {len(rel)} pairs above kinship threshold {threshold}")
    rel.to_csv(os.path.join(output_dir, "relatedness_report.csv"), index=False)
    return rel


def sample_qc(args):
    """Full sample-level QC."""
    os.makedirs(args.output, exist_ok=True)
    prefix = args.input
    if detect_input_type(args.input) == "vcf":
        prefix = os.path.join(args.output, "converted")
        vcf_to_plink(args.input, prefix)

    results = {}
    # 1. Missingness
    pass_s, fail_s = sample_missingness(prefix, args.output, args.sample_missing)
    results["missingness"] = {"pass": len(pass_s or []), "fail": len(fail_s or [])}
    # 2. Sex check
    sex_df = sex_check(prefix, args.output, args.sex_f, args.sex_m)
    if sex_df is not None:
        results["sexcheck"] = {"mismatches": int((sex_df["status"] == "mismatch").sum())}
    # 3. Heterozygosity
    het_df = heterozygosity(prefix, args.output, args.het_threshold)
    if het_df is not None:
        results["het"] = {"outliers": int((het_df["status"] == "outlier").sum())}
    # 4. Relatedness
    rel_df = relatedness(prefix, args.output, args.kinship_threshold)
    results["relatedness"] = {"pairs": len(rel_df) if rel_df is not None else 0}

    summary_path = os.path.join(args.output, "sample_qc_summary.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSample QC summary saved: {summary_path}")
    print(json.dumps(results, indent=2))


# ---- Variant QC ----
def variant_qc(args):
    """Variant-level QC: missingness, MAF, HWE."""
    os.makedirs(args.output, exist_ok=True)
    prefix = args.input
    if detect_input_type(args.input) == "vcf":
        prefix = os.path.join(args.output, "converted")
        vcf_to_plink(args.input, prefix)

    out_prefix = os.path.join(args.output, "filtered")
    filter_args = [
        "--bfile", prefix,
        "--make-bed",
        "--mind", str(args.sample_missing),
        "--geno", str(args.variant_missing),
        "--maf", str(args.maf),
        "--hwe", str(args.hwe),
        "--out", out_prefix,
    ]
    rc, out_text = run_plink(filter_args)
    if rc != 0:
        print(f"ERROR: {out_text}")
        return

    # Count before/after
    bim_before = prefix + ".bim"
    bim_after = out_prefix + ".bim"
    n_before = sum(1 for _ in open(bim_before)) if os.path.isfile(bim_before) else 0
    n_after = sum(1 for _ in open(bim_after)) if os.path.isfile(bim_after) else 0
    fam_before = prefix + ".fam"
    fam_after = out_prefix + ".fam"
    n_samples_before = sum(1 for _ in open(fam_before)) if os.path.isfile(fam_before) else 0
    n_samples_after = sum(1 for _ in open(fam_after)) if os.path.isfile(fam_after) else 0

    results = {
        "variants_before": n_before,
        "variants_after": n_after,
        "variants_removed": n_before - n_after,
        "samples_before": n_samples_before,
        "samples_after": n_samples_after,
        "samples_removed": n_samples_before - n_samples_after,
        "thresholds": {
            "sample_missing": args.sample_missing,
            "variant_missing": args.variant_missing,
            "maf": args.maf,
            "hwe": args.hwe,
        },
    }
    summary_path = os.path.join(args.output, "variant_qc_summary.json")
    with open(summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Variant QC: {n_before} → {n_after} variants ({n_before - n_after} removed)")
    print(f"Samples: {n_samples_before} → {n_samples_after} ({n_samples_before - n_samples_after} removed)")
    print(f"Filtered genotype: {out_prefix}.bed")
    print(f"Summary saved: {summary_path}")


# ---- Pipeline (full) ----
def pipeline_full(args):
    """Full QC pipeline: sample QC → variant QC → output."""
    os.makedirs(args.output, exist_ok=True)

    # Convert VCF if needed
    prefix = args.input
    if detect_input_type(args.input) == "vcf":
        prefix = os.path.join(args.output, "converted")
        print(f"Converting VCF to PLINK...")
        if not vcf_to_plink(args.input, prefix):
            return

    print("\n=== Step 1: Sample QC ===")
    sample_dir = os.path.join(args.output, "sample_qc")
    os.makedirs(sample_dir, exist_ok=True)
    sample_missingness(prefix, sample_dir, args.sample_missing)
    sex_check(prefix, sample_dir, args.sex_f, args.sex_m)
    heterozygosity(prefix, sample_dir, args.het_threshold)
    relatedness(prefix, sample_dir, args.kinship_threshold)

    print("\n=== Step 2: Variant QC ===")
    variant_dir = os.path.join(args.output, "variant_qc")
    os.makedirs(variant_dir, exist_ok=True)
    out_prefix = os.path.join(variant_dir, "filtered")
    filter_args = [
        "--bfile", prefix,
        "--make-bed",
        "--mind", str(args.sample_missing),
        "--geno", str(args.variant_missing),
        "--maf", str(args.maf),
        "--hwe", str(args.hwe),
        "--out", out_prefix,
    ]
    rc, out_text = run_plink(filter_args)
    if rc != 0:
        print(f"ERROR in variant filtering: {out_text}")
    else:
        n_before = sum(1 for _ in open(prefix + ".bim"))
        n_after = sum(1 for _ in open(out_prefix + ".bim"))
        n_samples = sum(1 for _ in open(out_prefix + ".fam"))
        print(f"Final: {n_after} variants, {n_samples} samples (from {n_before} variants)")

    print(f"\n=== QC Pipeline Complete ===")
    print(f"Results directory: {args.output}")
    print(f"Cleaned genotype: {out_prefix}.bed/.bim/.fam")


# ---- Convert ----
def convert_vcf2plink(args):
    """Convert VCF to PLINK format."""
    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    vcf_to_plink(args.input, args.output)


# ---- Report ----
def report_summary(args):
    """Generate QC summary report."""
    qc_dir = args.input
    report = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"), "qc_dir": qc_dir}

    # Collect JSON summaries
    for jf in ["sample_qc/sample_qc_summary.json", "variant_qc_summary.json"]:
        fp = os.path.join(qc_dir, jf)
        if os.path.isfile(fp):
            with open(fp) as f:
                report[os.path.basename(jf).replace(".json", "")] = json.load(f)

    # Collect CSV reports
    csv_files = []
    for root, dirs, files in os.walk(qc_dir):
        for fn in files:
            if fn.endswith("_report.csv"):
                csv_files.append(os.path.join(root, fn))
    report["report_files"] = csv_files

    # Write report
    report_path = args.output
    if report_path.endswith(".html"):
        html = "<html><body><h1>QC Summary Report</h1><pre>"
        html += json.dumps(report, indent=2)
        html += "</pre></body></html>"
        with open(report_path, "w") as f:
            f.write(html)
    else:
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)
    print(f"Report saved: {report_path}")


# ---- Main ----
def main():
    parser = argparse.ArgumentParser(
        description="Population Genotype QC",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="module", required=True)

    # pipeline
    p_pipe = sub.add_parser("pipeline", help="Full QC pipeline")
    p_pipe_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_pipe_sub.add_parser("full", help="Full pipeline (sample + variant QC)")
    add_common_args(p_full)

    # sample
    p_sample = sub.add_parser("sample", help="Sample-level QC")
    p_sample_sub = p_sample.add_subparsers(dest="subcommand", required=True)
    for name, help_text in [("qc", "Full sample QC"), ("sexcheck", "Sex check"),
                            ("het", "Heterozygosity"), ("relatedness", "IBD/kinship")]:
        sp = p_sample_sub.add_parser(name, help=help_text)
        add_common_args(sp)

    # variant
    p_variant = sub.add_parser("variant", help="Variant-level QC")
    p_variant_sub = p_variant.add_subparsers(dest="subcommand", required=True)
    sp = p_variant_sub.add_parser("qc", help="Variant filtering")
    add_common_args(sp)

    # convert
    p_convert = sub.add_parser("convert", help="Format conversion")
    p_convert_sub = p_convert.add_subparsers(dest="subcommand", required=True)
    p_v2p = p_convert_sub.add_parser("vcf2plink", help="VCF to PLINK")
    p_v2p.add_argument("--input", required=True, help="VCF file path")
    p_v2p.add_argument("--output", required=True, help="Output PLINK prefix")

    # report
    p_report = sub.add_parser("report", help="QC report")
    p_report_sub = p_report.add_subparsers(dest="subcommand", required=True)
    p_sum = p_report_sub.add_parser("summary", help="Generate summary report")
    p_sum.add_argument("--input", required=True, help="QC results directory")
    p_sum.add_argument("--output", required=True, help="Report output path")

    args = parser.parse_args()

    # Route
    if args.module == "pipeline" and args.subcommand == "full":
        pipeline_full(args)
    elif args.module == "sample":
        if args.subcommand == "qc":
            sample_qc(args)
        elif args.subcommand == "sexcheck":
            os.makedirs(args.output, exist_ok=True)
            prefix = args.input
            if detect_input_type(args.input) == "vcf":
                prefix = os.path.join(args.output, "converted")
                vcf_to_plink(args.input, prefix)
            sex_check(prefix, args.output, args.sex_f, args.sex_m)
        elif args.subcommand == "het":
            os.makedirs(args.output, exist_ok=True)
            prefix = args.input
            if detect_input_type(args.input) == "vcf":
                prefix = os.path.join(args.output, "converted")
                vcf_to_plink(args.input, prefix)
            heterozygosity(prefix, args.output, args.het_threshold)
        elif args.subcommand == "relatedness":
            os.makedirs(args.output, exist_ok=True)
            prefix = args.input
            if detect_input_type(args.input) == "vcf":
                prefix = os.path.join(args.output, "converted")
                vcf_to_plink(args.input, prefix)
            relatedness(prefix, args.output, args.kinship_threshold)
    elif args.module == "variant" and args.subcommand == "qc":
        variant_qc(args)
    elif args.module == "convert" and args.subcommand == "vcf2plink":
        convert_vcf2plink(args)
    elif args.module == "report" and args.subcommand == "summary":
        report_summary(args)


def add_common_args(p):
    p.add_argument("--input", required=True, help="Input VCF(.gz) or PLINK prefix")
    p.add_argument("--output", required=True, help="Output directory")
    p.add_argument("--sample-missing", type=float, default=0.02, help="Sample missing rate threshold (default: 0.02)")
    p.add_argument("--variant-missing", type=float, default=0.02, help="Variant missing rate threshold (default: 0.02)")
    p.add_argument("--maf", type=float, default=0.05, help="MAF threshold (default: 0.05)")
    p.add_argument("--hwe", type=float, default=1e-6, help="HWE p-value threshold (default: 1e-6)")
    p.add_argument("--het-threshold", type=float, default=3.0, help="Heterozygosity outlier SD (default: 3)")
    p.add_argument("--kinship-threshold", type=float, default=0.0884, help="Kinship threshold (default: 0.0884)")
    p.add_argument("--sex-f", type=float, default=0.2, help="F-stat female threshold (default: 0.2)")
    p.add_argument("--sex-m", type=float, default=0.8, help="F-stat male threshold (default: 0.8)")


if __name__ == "__main__":
    if not PLINK_BIN:
        print("WARNING: PLINK not found in PATH or common locations.")
        print("Install: conda install -c bioconda plink")
        print("Or:      pip install pandas-plink (Python wrapper)")
    main()
