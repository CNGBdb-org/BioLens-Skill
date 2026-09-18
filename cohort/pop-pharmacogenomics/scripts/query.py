#!/usr/bin/env python3
"""
Population Pharmacogenomics — query.py
=======================================
药物代谢酶 star allele 分型 + 表型预测。

依赖: pysam, pandas
"""
import argparse, os, sys, shutil, subprocess, json
import numpy as np
import pandas as pd

# ---- PGx SNP definitions (key variants for star allele calling) ----
# Format: gene -> {star_allele: [(rsID, position, ref, alt, genotype_required), ...]}
PGX_VARIANTS = {
    "CYP2D6": {
        "*3":  [("rs35742686", "T", "del")],
        "*4":  [("rs3892097", "G", "A"), ("rs1065852", "G", "A")],
        "*5":  [("rs5030862", "C", "del")],  # gene deletion
        "*10": [("rs1065852", "G", "A")],
        "*14": [("rs5030865", "G", "A")],
    },
    "CYP2C19": {
        "*2":  [("rs4244285", "G", "A")],
        "*3":  [("rs4986893", "G", "A")],
        "*17": [("rs12248560", "C", "T")],
    },
    "CYP2C9": {
        "*2":  [("rs1799853", "C", "T")],
        "*3":  [("rs1057910", "A", "C")],
    },
    "CYP3A5": {
        "*3":  [("rs776746", "A", "G")],
    },
    "SLCO1B1": {
        "*5":  [("rs4149056", "T", "C")],
    },
    "TPMT": {
        "*2":  [("rs1800462", "G", "C")],
        "*3A": [("rs1800460", "G", "A"), ("rs1142345", "T", "C")],
        "*3C": [("rs1142345", "T", "C")],
    },
}

# Diplotype -> phenotype mapping (simplified)
DIPLOTYPE_PHENOTYPE = {
    "CYP2D6": {
        ("*4/*4", "*5/*5", "*4/*5"): "Poor Metabolizer (PM)",
        ("*10/*10", "*4/*10", "*5/*10"): "Intermediate Metabolizer (IM)",
        ("*1/*1", "*1/*2", "*2/*2"): "Normal Metabolizer (NM)",
        ("*1/*1x2", "*1/*2x2"): "Ultrarapid Metabolizer (UM)",
    },
    "CYP2C19": {
        ("*2/*2", "*2/*3", "*3/*3"): "Poor Metabolizer (PM)",
        ("*1/*2", "*1/*3"): "Intermediate Metabolizer (IM)",
        ("*1/*1", "*1/*17"): "Normal Metabolizer (NM)",
        ("*17/*17"): "Rapid Metabolizer (RM)",
    },
    "CYP2C9": {
        ("*2/*2", "*2/*3", "*3/*3"): "Poor Metabolizer (PM)",
        ("*1/*2", "*1/*3"): "Intermediate Metabolizer (IM)",
        ("*1/*1"): "Normal Metabolizer (NM)",
    },
    "CYP3A5": {
        ("*3/*3"): "Poor Metabolizer (PM)",
        ("*1/*3"): "Intermediate Metabolizer (IM)",
        ("*1/*1"): "Normal Metabolizer (NM)",
    },
    "SLCO1B1": {
        ("*5/*5"): "Decreased Function",
        ("*1/*5"): "Intermediate Function",
        ("*1/*1"): "Normal Function",
    },
    "TPMT": {
        ("*2/*2", "*3A/*3A", "*3C/*3C", "*2/*3A", "*2/*3C", "*3A/*3C"): "Poor Metabolizer (PM)",
        ("*1/*2", "*1/*3A", "*1/*3C"): "Intermediate Metabolizer (IM)",
        ("*1/*1"): "Normal Metabolizer (NM)",
    },
}

# Drug dosing recommendations (simplified, from CPIC)
DRUG_RECOMMENDATIONS = {
    "codeine": {
        "gene": "CYP2D6",
        "PM": "Avoid codeine; use alternative analgesic",
        "IM": "Use alternative analgesic; if codeine needed, label-use dose",
        "NM": "Standard dosing",
        "UM": "Avoid codeine due to risk of toxicity",
    },
    "clopidogrel": {
        "gene": "CYP2C19",
        "PM": "Avoid clopidogrel; use alternative antiplatelet (prasugrel/ticagrelor)",
        "IM": "Consider alternative antiplatelet",
        "NM": "Standard dosing",
        "RM": "Standard dosing",
    },
    "warfarin": {
        "gene": "CYP2C9",
        "PM": "Reduce starting dose by 30-50%",
        "IM": "Reduce starting dose by 20-30%",
        "NM": "Standard dosing",
    },
    "tacrolimus": {
        "gene": "CYP3A5",
        "PM": "Standard dosing",
        "IM": "Increase starting dose 1.5-2x",
        "NM": "Increase starting dose 1.5-2x",
    },
    "simvastatin": {
        "gene": "SLCO1B1",
        "Decreased Function": "Prescribe lower dose or alternative statin",
        "Intermediate Function": "Consider lower dose",
        "Normal Function": "Standard dosing",
    },
    "azathioprine": {
        "gene": "TPMT",
        "PM": "Avoid; start with 10% of standard dose or use alternative",
        "IM": "Reduce starting dose by 30-70%",
        "NM": "Standard dosing",
    },
}


def call_star_alleles(vcf_file, gene, output_dir):
    """Call star alleles for a gene from VCF."""
    import pysam
    os.makedirs(output_dir, exist_ok=True)
    if gene not in PGX_VARIANTS:
        print(f"ERROR: gene {gene} not supported. Supported: {list(PGX_VARIANTS.keys())}")
        return None
    try:
        vcf = pysam.VariantFile(vcf_file)
    except Exception as e:
        print(f"ERROR opening VCF: {e}")
        return None
    variants = PGX_VARIANTS[gene]
    results = []
    for sample in vcf.header.samples:
        alleles = []
        for star_allele, snp_list in variants.items():
            has_allele = True
            for rsid, ref, alt in snp_list:
                found = False
                vcf.reset()  # Reset to beginning
                for rec in vcf:
                    if rec.id == rsid or rsid in str(rec.id or ""):
                        gt = rec.samples[sample]["GT"]
                        alt_count = sum(1 for g in gt if g is not None and g > 0)
                        if alt_count > 0:
                            found = True
                            break
                if not found:
                    has_allele = False
                    break
            if has_allele:
                alleles.append(star_allele)
        if not alleles:
            alleles = ["*1"]  # Default = normal function
        diplotype = "/".join(sorted(alleles[:2]))
        results.append({"Sample": sample, "Gene": gene, "Diplotype": diplotype,
                        "StarAlleles": ",".join(alleles)})
    df = pd.DataFrame(results)
    result_file = os.path.join(output_dir, f"{gene}_genotype.tsv")
    df.to_csv(result_file, sep="\t", index=False)
    print(f"{gene} genotyping: {len(df)} samples")
    if len(df) > 0:
        print(f"  Diplotype distribution: {df['Diplotype'].value_counts().to_dict()}")
    return result_file


def predict_phenotype(genotype_file, output_dir):
    """Predict metabolizer phenotype from diplotype."""
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(genotype_file, sep="\t")
    gene = df["Gene"].iloc[0] if "Gene" in df.columns else "CYP2D6"
    pheno_map = DIPLOTYPE_PHENOTYPE.get(gene, {})
    def get_phenotype(diplotype):
        for dlist, phenotype in pheno_map.items():
            if any(d.lower() in diplotype.lower() for d in dlist):
                return phenotype
        return "Normal Metabolizer (NM)"
    df["Phenotype"] = df["Diplotype"].apply(get_phenotype)
    result_file = os.path.join(output_dir, f"{gene}_phenotype.tsv")
    df.to_csv(result_file, sep="\t", index=False)
    print(f"{gene} phenotype: {len(df)} samples")
    if len(df) > 0:
        print(f"  Phenotype distribution: {df['Phenotype'].value_counts().to_dict()}")
    return result_file


def population_summary(vcf_file, output_dir):
    """Population PGx summary across all supported genes."""
    os.makedirs(output_dir, exist_ok=True)
    all_results = []
    for gene in PGX_VARIANTS.keys():
        print(f"Processing {gene}...")
        geno_file = call_star_alleles(vcf_file, gene, os.path.join(output_dir, gene))
        if geno_file:
            pheno_file = predict_phenotype(geno_file, os.path.join(output_dir, gene))
            if pheno_file:
                df = pd.read_csv(pheno_file, sep="\t")
                all_results.append(df)
    if all_results:
        combined = pd.concat(all_results, ignore_index=True)
        summary_file = os.path.join(output_dir, "pgx_summary.tsv")
        combined.to_csv(summary_file, sep="\t", index=False)
        print(f"\nPGx summary: {summary_file} ({len(combined)} records)")
        # Frequency table
        freq = combined.groupby(["Gene", "Diplotype", "Phenotype"]).size().reset_index(name="count")
        freq_file = os.path.join(output_dir, "pgx_frequency.tsv")
        freq.to_csv(freq_file, sep="\t", index=False)
        print(f"Frequency table: {freq_file}")
        return summary_file
    return None


def dosing_recommend(genotype_file, drug, output_dir):
    """Drug dosing recommendations based on genotype."""
    os.makedirs(output_dir, exist_ok=True)
    if drug not in DRUG_RECOMMENDATIONS:
        print(f"Drug '{drug}' not in database. Supported: {list(DRUG_RECOMMENDATIONS.keys())}")
        return None
    drug_info = DRUG_RECOMMENDATIONS[drug]
    gene = drug_info["gene"]
    df = pd.read_csv(genotype_file, sep="\t")
    def get_dosing(phenotype):
        for key, rec in drug_info.items():
            if key in phenotype or phenotype in key:
                return rec
        return drug_info.get("NM", "Standard dosing")
    df["Drug"] = drug
    df["Recommendation"] = df["Phenotype"].apply(get_dosing) if "Phenotype" in df.columns else "N/A"
    result_file = os.path.join(output_dir, f"{drug}_dosing.tsv")
    df.to_csv(result_file, sep="\t", index=False)
    print(f"Dosing recommendations for {drug}: {len(df)} samples")
    if len(df) > 0 and "Recommendation" in df.columns:
        print(f"  Distribution: {df['Recommendation'].value_counts().to_dict()}")
    return result_file


def pipeline_full(args):
    os.makedirs(args.output, exist_ok=True)
    print("=== PGx Star Allele Calling ===")
    population_summary(args.vcf, os.path.join(args.output, "pgx"))
    print(f"\n=== PGx Analysis Complete ===")
    print(f"  Results: {args.output}")

def main():
    parser = argparse.ArgumentParser(description="Population Pharmacogenomics")
    sub = parser.add_subparsers(dest="module", required=True)
    p_pipe = sub.add_parser("pipeline"); p_sub = p_pipe.add_subparsers(dest="subcommand", required=True)
    p_full = p_sub.add_parser("full")
    p_full.add_argument("--vcf", required=True); p_full.add_argument("--output", required=True)
    p_gt = sub.add_parser("genotype"); p_gt_sub = p_gt.add_subparsers(dest="subcommand", required=True)
    p_gc = p_gt_sub.add_parser("call")
    p_gc.add_argument("--vcf", required=True)
    p_gc.add_argument("--gene", required=True, choices=list(PGX_VARIANTS.keys()))
    p_gc.add_argument("--output", required=True)
    p_ph = sub.add_parser("phenotype"); p_ph_sub = p_ph.add_subparsers(dest="subcommand", required=True)
    p_pc = p_ph_sub.add_parser("predict")
    p_pc.add_argument("--genotype", required=True); p_pc.add_argument("--output", required=True)
    p_pop = sub.add_parser("population"); p_pop_sub = p_pop.add_subparsers(dest="subcommand", required=True)
    p_ps = p_pop_sub.add_parser("summary")
    p_ps.add_argument("--vcf", required=True); p_ps.add_argument("--output", required=True)
    p_do = sub.add_parser("dosing"); p_do_sub = p_do.add_subparsers(dest="subcommand", required=True)
    p_dr = p_do_sub.add_parser("recommend")
    p_dr.add_argument("--genotype", required=True)
    p_dr.add_argument("--drug", required=True, choices=list(DRUG_RECOMMENDATIONS.keys()))
    p_dr.add_argument("--output", required=True)
    args = parser.parse_args()
    if args.module == "pipeline" and args.subcommand == "full": pipeline_full(args)
    elif args.module == "genotype" and args.subcommand == "call":
        call_star_alleles(args.vcf, args.gene, args.output)
    elif args.module == "phenotype" and args.subcommand == "predict":
        predict_phenotype(args.genotype, args.output)
    elif args.module == "population" and args.subcommand == "summary":
        population_summary(args.vcf, args.output)
    elif args.module == "dosing" and args.subcommand == "recommend":
        dosing_recommend(args.genotype, args.drug, args.output)

if __name__ == "__main__":
    main()
