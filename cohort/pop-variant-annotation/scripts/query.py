#!/usr/bin/env python3
"""
Population Variant Annotation — query.py
=========================================
变异功能注释主入口脚本。
自动检测 VEP → ANNOVAR → SnpEff → bcftools csq → pysam。

依赖: pysam, pandas
可选: VEP, ANNOVAR, SnpEff, bcftools
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
              "/usr/bin", "/usr/local/bin"]:
        fp = os.path.join(d, name)
        if os.path.isfile(fp) and os.access(fp, os.X_OK): return fp
    return None

VEP_BIN = find_tool("vep")
ANNOVAR_BIN = find_tool("table_annovar.pl")
SNPEFF_BIN = find_tool("snpEff") or find_tool("snpeff")
BCFTOOLS_BIN = find_tool("bcftools")


def annotate_vep(vcf_file, output_dir, genome="GRCh38"):
    """Annotate using Ensembl VEP."""
    if not VEP_BIN:
        print("VEP not found. Install: conda install -c bioconda ensembl-vep")
        return annotate_pysam(vcf_file, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "annotated.vcf")
    cmd = [VEP_BIN, "-i", vcf_file, "-o", out_file,
           "--format", "vcf", "--vcf", "--symbol", "--numbers",
           "--assembly", genome, "--cache", "--offline",
           "--force_overwrite"]
    print(f"Running VEP ({genome})...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if r.returncode != 0:
            print(f"VEP failed: {r.stderr[:500]}")
            return annotate_pysam(vcf_file, output_dir)
        print(f"VEP annotation complete: {out_file}")
        return out_file
    except subprocess.TimeoutExpired:
        print("VEP timed out")
        return annotate_pysam(vcf_file, output_dir)


def annotate_annovar(vcf_file, output_dir, genome="GRCh38"):
    """Annotate using ANNOVAR."""
    if not ANNOVAR_BIN:
        print("ANNOVAR not found. Install: https://annovar.openbioinformatics.org/")
        return annotate_pysam(vcf_file, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    # Convert VCF to ANNOVAR input
    convert_cmd = os.path.join(os.path.dirname(ANNOVAR_BIN), "convert2annovar.pl")
    avinput = os.path.join(output_dir, "input.avinput")
    conv = [convert_cmd, "--format", "vcf4", "--include", "info",
            "--outfile", avinput, vcf_file]
    try:
        subprocess.run(conv, capture_output=True, text=True, timeout=600)
    except Exception as e:
        print(f"ANNOVAR conversion failed: {e}")
        return annotate_pysam(vcf_file, output_dir)
    db = genome.lower()
    out_prefix = os.path.join(output_dir, "annotated")
    cmd = [ANNOVAR_BIN, avinput, os.path.dirname(ANNOVAR_BIN) + "/humandb/",
           "-buildver", db, "-out", out_prefix,
           "-remove", "-protocol", "refGene,cytoBand,gnomad_genome",
           "-operation", "g,r,f", "-nastring", "."]
    print(f"Running ANNOVAR ({genome})...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=7200)
        if r.returncode != 0:
            print(f"ANNOVAR failed: {r.stderr[:500]}")
            return annotate_pysam(vcf_file, output_dir)
        result_file = out_prefix + ".hg38_multianno.txt"
        if not os.path.isfile(result_file):
            result_file = out_prefix + ".hg19_multianno.txt"
        print(f"ANNOVAR annotation complete: {result_file}")
        return result_file
    except subprocess.TimeoutExpired:
        print("ANNOVAR timed out")
        return annotate_pysam(vcf_file, output_dir)


def annotate_snpeff(vcf_file, output_dir, genome="GRCh38"):
    """Annotate using SnpEff."""
    if not SNPEFF_BIN:
        print("SnpEff not found. Install: conda install -c bioconda snpeff")
        return annotate_pysam(vcf_file, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "annotated.vcf")
    genome_map = {"GRCh38": "hg38", "GRCh37": "hg19"}
    snpeff_genome = genome_map.get(genome, "hg38")
    cmd = ["java", "-jar", SNPEFF_BIN, snpeff_genome, vcf_file]
    print(f"Running SnpEff ({snpeff_genome})...")
    try:
        with open(out_file, "w") as f:
            r = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True, timeout=7200)
        if r.returncode != 0:
            print(f"SnpEff failed: {r.stderr[:500]}")
            return annotate_pysam(vcf_file, output_dir)
        print(f"SnpEff annotation complete: {out_file}")
        return out_file
    except subprocess.TimeoutExpired:
        print("SnpEff timed out")
        return annotate_pysam(vcf_file, output_dir)


def annotate_bcftools(vcf_file, output_dir):
    """Annotate using bcftools csq."""
    if not BCFTOOLS_BIN:
        print("bcftools not found. Install: conda install -c bioconda bcftools")
        return annotate_pysam(vcf_file, output_dir)
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "annotated.vcf")
    cmd = [BCFTOOLS_BIN, "csq", "-f", vcf_file, "-o", out_file]
    print(f"Running bcftools csq...")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
        if r.returncode != 0:
            print(f"bcftools csq failed: {r.stderr[:500]}")
            return annotate_pysam(vcf_file, output_dir)
        print(f"bcftools annotation complete: {out_file}")
        return out_file
    except subprocess.TimeoutExpired:
        print("bcftools timed out")
        return annotate_pysam(vcf_file, output_dir)


def annotate_pysam(vcf_file, output_dir):
    """Basic annotation using pysam (no external tools needed)."""
    import pysam
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "annotated_basic.tsv")
    records = []
    try:
        vcf = pysam.VariantFile(vcf_file)
    except Exception as e:
        # Try plain VCF (not bgzipped)
        vcf = pysam.VariantFile("-")
        print(f"Could not open {vcf_file}: {e}")
        return None
    for rec in vcf:
        info = {
            "CHROM": rec.chrom, "POS": rec.pos, "ID": rec.id if rec.id else ".",
            "REF": rec.ref, "ALT": ",".join(rec.alts) if rec.alts else ".",
            "QUAL": rec.qual if rec.qual else ".",
        }
        # Extract info fields
        for key in rec.info:
            try:
                info[key] = rec.info[key]
            except Exception:
                info[key] = "."
        # Basic consequence inference
        ref_len = len(rec.ref)
        alt_lens = [len(a) for a in rec.alts] if rec.alts else [0]
        if ref_len == 1 and all(l == 1 for l in alt_lens):
            info["VariantType"] = "SNV"
        elif ref_len != alt_lens[0] if alt_lens else True:
            info["VariantType"] = "INDEL"
        else:
            info["VariantType"] = "MNV"
        records.append(info)
    df = pd.DataFrame(records)
    df.to_csv(out_file, sep="\t", index=False)
    print(f"Basic annotation (pysam) complete: {out_file}")
    print(f"  {len(df)} variants annotated")
    if "VariantType" in df.columns:
        vt = df["VariantType"].value_counts()
        for k, v in vt.items():
            print(f"  {k}: {v}")
    return out_file


def annotate_list(variants_file, output_dir):
    """Annotate a list of variants (chr:pos ref alt or rsID)."""
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "annotated_list.tsv")
    records = []
    with open(variants_file) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 4:
                records.append({"CHROM": parts[0], "POS": int(parts[1]),
                               "REF": parts[2], "ALT": parts[3],
                               "VariantType": "SNV" if len(parts[2]) == len(parts[3]) == 1 else "INDEL"})
            elif len(parts) == 1 and parts[0].startswith("rs"):
                records.append({"rsID": parts[0]})
    df = pd.DataFrame(records)
    df.to_csv(out_file, sep="\t", index=False)
    print(f"Annotated {len(df)} variants from list: {out_file}")
    return out_file


def report_summary(annotated_dir, output_file):
    """Generate annotation summary."""
    summary = {"annotated_dir": annotated_dir}
    for root, dirs, files in os.walk(annotated_dir):
        for fn in files:
            fp = os.path.join(root, fn)
            if fn.endswith(".tsv") or fn.endswith(".txt"):
                try:
                    df = pd.read_csv(fp, sep="\t", nrows=100)
                    summary[fn] = {"n_rows_sampled": len(df), "columns": list(df.columns)}
                except Exception:
                    pass
    with open(output_file, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Summary saved: {output_file}")


def pipeline_full(args):
    """Full annotation pipeline: auto-detect best tool → annotate → summary."""
    os.makedirs(args.output, exist_ok=True)
    print("=== Step 1: Tool Detection ===")
    tool_used = "pysam"
    if VEP_BIN:
        tool_used = "vep"
        print(f"Using VEP: {VEP_BIN}")
    elif SNPEFF_BIN:
        tool_used = "snpeff"
        print(f"Using SnpEff: {SNPEFF_BIN}")
    elif BCFTOOLS_BIN:
        tool_used = "bcftools"
        print(f"Using bcftools: {BCFTOOLS_BIN}")
    elif ANNOVAR_BIN:
        tool_used = "annovar"
        print(f"Using ANNOVAR: {ANNOVAR_BIN}")
    else:
        print("No external annotation tool found. Using pysam basic annotation.")
        print("Install: conda install -c bioconda ensembl-vep snpeff bcftools")

    print(f"\n=== Step 2: Annotation ({tool_used}) ===")
    if tool_used == "vep":
        result = annotate_vep(args.input, args.output, args.genome)
    elif tool_used == "snpeff":
        result = annotate_snpeff(args.input, args.output, args.genome)
    elif tool_used == "bcftools":
        result = annotate_bcftools(args.input, args.output)
    elif tool_used == "annovar":
        result = annotate_annovar(args.input, args.output, args.genome)
    else:
        result = annotate_pysam(args.input, args.output)

    print(f"\n=== Step 3: Summary ===")
    if result:
        report_summary(args.output, os.path.join(args.output, "annotation_summary.json"))
    print(f"\n=== Annotation Complete ===")
    print(f"  Tool: {tool_used}")
    print(f"  Result: {result}")


def main():
    parser = argparse.ArgumentParser(description="Population Variant Annotation")
    sub = parser.add_subparsers(dest="module", required=True)

    # pipeline
    p_pipe = sub.add_parser("pipeline")
    p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full")
    p_full.add_argument("--input", required=True, help="VCF file")
    p_full.add_argument("--output", required=True)
    p_full.add_argument("--genome", default="GRCh38", choices=["GRCh37", "GRCh38"])

    # annotate
    p_ann = sub.add_parser("annotate")
    p_ann_sub = p_ann.add_subparsers(dest="subcommand", required=True)
    for tool in ["vep", "annovar", "snpeff", "bcftools", "pysam"]:
        sp = p_ann_sub.add_parser(tool)
        sp.add_argument("--input", required=True)
        sp.add_argument("--output", required=True)
        sp.add_argument("--genome", default="GRCh38", choices=["GRCh37", "GRCh38"])
    p_list = p_ann_sub.add_parser("list")
    p_list.add_argument("--input", required=True, help="Variant list file")
    p_list.add_argument("--output", required=True)

    # report
    p_rep = sub.add_parser("report")
    p_rep_sub = p_rep.add_subparsers(dest="subcommand", required=True)
    p_sum = p_rep_sub.add_parser("summary")
    p_sum.add_argument("--input", required=True)
    p_sum.add_argument("--output", required=True)

    args = parser.parse_args()

    if args.module == "pipeline" and args.subcommand == "full":
        pipeline_full(args)
    elif args.module == "annotate":
        if args.subcommand == "vep":
            annotate_vep(args.input, args.output, args.genome)
        elif args.subcommand == "annovar":
            annotate_annovar(args.input, args.output, args.genome)
        elif args.subcommand == "snpeff":
            annotate_snpeff(args.input, args.output, args.genome)
        elif args.subcommand == "bcftools":
            annotate_bcftools(args.input, args.output)
        elif args.subcommand == "pysam":
            annotate_pysam(args.input, args.output)
        elif args.subcommand == "list":
            annotate_list(args.input, args.output)
    elif args.module == "report" and args.subcommand == "summary":
        report_summary(args.input, args.output)


if __name__ == "__main__":
    main()
