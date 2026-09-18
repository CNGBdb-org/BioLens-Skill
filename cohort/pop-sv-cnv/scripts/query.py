#!/usr/bin/env python3
"""
Population SV & CNV — query.py
===============================
结构变异 + 拷贝数变异检测与分析。

依赖: pysam, pandas
可选: DELLY, Manta, GATK-gCNV, PennCNV
"""
import argparse, os, sys, shutil, subprocess, json
from pathlib import Path
import numpy as np
import pandas as pd

def find_tool(name):
    p = shutil.which(name)
    if p: return p
    for d in [os.path.expanduser("~/software/miniforge/envs/cima/bin"),
              os.path.expanduser("~/software/miniforge/bin"),
              os.path.expanduser("~/software"),
              "/usr/bin", "/usr/local/bin"]:
        fp = os.path.join(d, name)
        if os.path.isfile(fp) and os.access(fp, os.X_OK): return fp
    return None

DELLY_BIN = find_tool("delly")
MANTA_BIN = find_tool("configManta.py") or find_tool("manta")

# ---- SV detection ----
def sv_detect(bam_list, output_dir, tool="delly", min_size=50):
    """Detect SVs using DELLY or Manta."""
    os.makedirs(output_dir, exist_ok=True)
    bcf_out = os.path.join(output_dir, "sv_calls.bcf")
    if tool == "delly" and DELLY_BIN:
        cmd = [DELLY_BIN, "call", "--bcf", bcf_out,
               "--genome", "GRCh38", "--bamlist", bam_list,
               "--minsize", str(min_size)]
        print("Running DELLY SV detection...")
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=43200)
            if r.returncode == 0 and os.path.isfile(bcf_out):
                print(f"DELLY complete: {bcf_out}")
                return bcf_out
            print(f"DELLY failed: {r.stderr[:500]}")
        except subprocess.TimeoutExpired:
            print("DELLY timed out")
    elif tool == "manta" and MANTA_BIN:
        print("Manta requires configuration step. Please refer to Manta documentation.")
    # Fallback: parse existing SV VCF with pysam
    print("No SV caller found. Install: conda install -c bioconda delly")
    print("Or provide pre-called SV VCF for analysis.")
    return None

# ---- CNV calling ----
def cnv_call(vcf_file, output_dir):
    """CNV calling from VCF or BAM."""
    os.makedirs(output_dir, exist_ok=True)
    # Try GATK-gCNV (simplified)
    gatkcnv = find_tool("gatk")
    if gatkcnv:
        print("GATK-gCNV requires preprocessing (CollectReadCounts). Refer to GATK docs.")
    # Fallback: parse CNV from VCF INFO/SVTYPE
    import pysam
    try:
        vcf = pysam.VariantFile(vcf_file)
    except Exception as e:
        print(f"ERROR opening VCF: {e}")
        return None
    records = []
    for rec in vcf:
        svtype = rec.info.get("SVTYPE", [None])[0] if "SVTYPE" in rec.info else None
        svlen = rec.info.get("SVLEN", [0])[0] if "SVLEN" in rec.info else 0
        cn = rec.info.get("CN", [None])[0] if "CN" in rec.info else None
        if svtype or cn:
            records.append({
                "CHROM": rec.chrom, "POS": rec.pos,
                "ID": rec.id if rec.id else ".",
                "REF": rec.ref, "ALT": ",".join(rec.alts) if rec.alts else ".",
                "SVTYPE": svtype, "SVLEN": svlen, "CN": cn,
            })
    df = pd.DataFrame(records)
    out_file = os.path.join(output_dir, "cnv_calls.tsv")
    df.to_csv(out_file, sep="\t", index=False)
    print(f"CNV/SV parsed: {len(df)} variants")
    if len(df) > 0 and "SVTYPE" in df.columns:
        print(f"  By type: {df['SVTYPE'].value_counts().to_dict()}")
    return out_file

# ---- Frequency ----
def freq_compute(sv_vcf, output_dir, min_af=0.01):
    """Compute SV/CNV population frequency."""
    import pysam
    os.makedirs(output_dir, exist_ok=True)
    try:
        vcf = pysam.VariantFile(sv_vcf)
    except Exception as e:
        print(f"ERROR: {e}")
        return None
    records = []
    n_samples = len(list(vcf.header.samples))
    for rec in vcf:
        # Count carriers
        carriers = 0
        for sample in vcf.header.samples:
            gt = rec.samples[sample]["GT"]
            if gt[0] is not None and gt[0] != "." and gt[0] != 0:
                carriers += 1
            elif len(gt) > 1 and gt[1] is not None and gt[1] != "." and gt[1] != 0:
                carriers += 1
        af = carriers / n_samples if n_samples > 0 else 0
        svtype = rec.info.get("SVTYPE", [None])[0] if "SVTYPE" in rec.info else None
        records.append({
            "CHROM": rec.chrom, "POS": rec.pos, "ID": rec.id,
            "SVTYPE": svtype, "carriers": carriers,
            "n_samples": n_samples, "AF": af,
        })
    df = pd.DataFrame(records)
    if min_af > 0 and len(df) > 0:
        df = df[df["AF"].astype(float) >= min_af]
    out_file = os.path.join(output_dir, "sv_freq.tsv")
    df.to_csv(out_file, sep="\t", index=False)
    print(f"SV frequency: {len(df)} variants (min AF={min_af}, n_samples={n_samples})")
    return out_file

# ---- Annotation ----
def annotate_sv(sv_vcf, output_dir):
    """Annotate SVs with gene overlap."""
    import pysam
    os.makedirs(output_dir, exist_ok=True)
    # Load gene annotation if available
    gene_file = None
    for p in ["/public/database/refseq/NCBI_GRCh38.genes.loc",
              "/public/database/gencode/gencode_v40.genes.bed"]:
        if os.path.isfile(p):
            gene_file = p
            break
    genes = []
    if gene_file:
        with open(gene_file) as f:
            for line in f:
                if line.startswith("#"): continue
                parts = line.strip().split("\t")
                genes.append((parts[0], int(parts[1]), int(parts[2]), parts[3] if len(parts)>3 else "."))
    try:
        vcf = pysam.VariantFile(sv_vcf)
    except Exception as e:
        print(f"ERROR: {e}")
        return None
    records = []
    for rec in vcf:
        svtype = rec.info.get("SVTYPE", [None])[0] if "SVTYPE" in rec.info else None
        svend = rec.info.get("END", [rec.pos])[0] if "END" in rec.info else rec.pos
        # Find overlapping genes
        overlapping = []
        for gchr, gstart, gend, gname in genes:
            if rec.chrom == gchr and rec.pos <= gend and svend >= gstart:
                overlapping.append(gname)
        records.append({
            "CHROM": rec.chrom, "POS": rec.pos, "END": svend,
            "SVTYPE": svtype, "overlapping_genes": ",".join(overlapping[:10]),
            "n_genes": len(overlapping),
        })
    df = pd.DataFrame(records)
    out_file = os.path.join(output_dir, "sv_annotated.tsv")
    df.to_csv(out_file, sep="\t", index=False)
    print(f"SV annotation: {len(df)} variants annotated")
    if len(df) > 0:
        print(f"  With gene overlap: {(df['n_genes'] > 0).sum()}")
    return out_file

# ---- Pipeline ----
def pipeline_full(args):
    os.makedirs(args.output, exist_ok=True)
    print("=== Step 1: SV Detection ===")
    sv_file = sv_detect(args.bam, os.path.join(args.output, "sv"), args.tool)
    if args.vcf:
        print("\n=== Step 1b: Parse existing SV/CNV VCF ===")
        cnv_file = cnv_call(args.vcf, os.path.join(args.output, "cnv"))
        if cnv_file:
            print("\n=== Step 2: Frequency ===")
            freq_compute(args.vcf, os.path.join(args.output, "freq"))
            print("\n=== Step 3: Annotation ===")
            annotate_sv(args.vcf, os.path.join(args.output, "annot"))
    print(f"\n=== SV/CNV Analysis Complete ===")
    print(f"  Results: {args.output}")

def main():
    parser = argparse.ArgumentParser(description="Population SV & CNV")
    sub = parser.add_subparsers(dest="module", required=True)
    p_pipe = sub.add_parser("pipeline"); p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full")
    p_full.add_argument("--bam", help="BAM list file")
    p_full.add_argument("--vcf", help="Existing SV/CNV VCF")
    p_full.add_argument("--output", required=True)
    p_full.add_argument("--tool", default="delly", choices=["delly", "manta"])
    p_full.add_argument("--min-size", type=int, default=50)
    p_sv = sub.add_parser("sv"); p_sv_sub = p_sv.add_subparsers(dest="subcommand", required=True)
    p_sd = p_sv_sub.add_parser("detect")
    p_sd.add_argument("--bam", required=True); p_sd.add_argument("--output", required=True)
    p_sd.add_argument("--tool", default="delly", choices=["delly", "manta"])
    p_sd.add_argument("--min-size", type=int, default=50)
    p_cnv = sub.add_parser("cnv"); p_cnv_sub = p_cnv.add_subparsers(dest="subcommand", required=True)
    p_cc = p_cnv_sub.add_parser("call")
    p_cc.add_argument("--vcf", required=True); p_cc.add_argument("--output", required=True)
    p_fq = sub.add_parser("freq"); p_fq_sub = p_fq.add_subparsers(dest="subcommand", required=True)
    p_fc = p_fq_sub.add_parser("compute")
    p_fc.add_argument("--sv", required=True); p_fc.add_argument("--output", required=True)
    p_fc.add_argument("--min-af", type=float, default=0.01)
    p_an = sub.add_parser("annotate"); p_an_sub = p_an.add_subparsers(dest="subcommand", required=True)
    p_as = p_an_sub.add_parser("sv")
    p_as.add_argument("--sv", required=True); p_as.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.module == "pipeline" and args.subcommand == "full": pipeline_full(args)
    elif args.module == "sv" and args.subcommand == "detect":
        sv_detect(args.bam, args.output, args.tool, args.min_size)
    elif args.module == "cnv" and args.subcommand == "call":
        cnv_call(args.vcf, args.output)
    elif args.module == "freq" and args.subcommand == "compute":
        freq_compute(args.sv, args.output, args.min_af)
    elif args.module == "annotate" and args.subcommand == "sv":
        annotate_sv(args.sv, args.output)

if __name__ == "__main__":
    main()
