#!/usr/bin/env python3
"""
生成 demo 示例数据
==================
小型 VCF + 表型 + 协变量 + sumstats + eQTL + 群体标签。
用于测试 cohort pipeline 和各个 skill。

生成:
  data/demo_genotype.vcf.gz   — 50 样本 × ~500 SNP（chr1-22）
  data/demo_pheno.txt          — 表型（连续型 + 二分类）
  data/demo_covar.txt          — 协变量（age/sex/PC1-PC10）
  data/demo_sumstats.txt       — GWAS summary stats
  data/demo_eqtl.txt           — eQTL summary stats
  data/demo_pop.txt            — 群体标签（EAS/EUR/AFR）
  data/demo_pheno_binary.txt   — 二分类表型
"""
import os
import sys
import random
import gzip
import numpy as np
import pandas as pd

random.seed(42)
np.random.seed(42)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT_DIR, exist_ok=True)

N_SAMPLES = 50
N_SNPS = 500

# ---- 1. 生成 VCF ----
def generate_vcf():
    """Generate a small VCF with 50 samples × 500 SNPs across chr1-22."""
    samples = [f"sample_{i:03d}" for i in range(N_SAMPLES)]
    # SNP positions: ~23 SNPs per chromosome
    snps = []
    for chrom in range(1, 23):
        n_chr = N_SNPS // 22
        for j in range(n_chr):
            pos = random.randint(1_000_000, 250_000_000)
            rsid = f"rs{random.randint(100000, 9999999)}"
            ref = random.choice("ACGT")
            alt = random.choice([a for a in "ACGT" if a != ref])
            snps.append((chrom, pos, rsid, ref, alt))
    vcf_lines = [
        "##fileformat=VCFv4.2",
        "##source=cohort_pipeline_demo",
        '##INFO=<ID=AF,Number=1,Type=Float,Description="Allele Frequency">',
    ]
    for chrom in range(1, 23):
        vcf_lines.append(f"##contig=<ID={chrom},length=250000000>")
    header = "\t".join(["#CHROM", "POS", "ID", "REF", "ALT", "QUAL", "FILTER", "INFO", "FORMAT"] + samples)
    vcf_lines.append(header)
    for chrom, pos, rsid, ref, alt in snps:
        af = round(random.uniform(0.05, 0.5), 4)
        gt_line = f"{chrom}\t{pos}\t{rsid}\t{ref}\t{alt}\t.\tPASS\tAF={af}\tGT"
        for _ in range(N_SAMPLES):
            # Generate genotype based on AF
            g1 = 1 if random.random() < af else 0
            g2 = 1 if random.random() < af else 0
            gt_line += f"\t{g1}|{g2}"
        vcf_lines.append(gt_line)
    # Write plain VCF then bgzip
    vcf_path = os.path.join(OUT_DIR, "demo_genotype.vcf")
    with open(vcf_path, "w") as f:
        f.write("\n".join(vcf_lines) + "\n")
    # Try bgzip
    import shutil
    bgzip = shutil.which("bgzip") or shutil.which("htsfile")
    if bgzip:
        os.system(f"{bgzip} -f {vcf_path}")
        vcf_gz = vcf_path + ".gz"
    else:
        # Just rename
        vcf_gz = vcf_path + ".gz"
        os.system(f"gzip -c {vcf_path} > {vcf_gz}")
    print(f"VCF: {vcf_gz} ({len(snps)} SNPs, {N_SAMPLES} samples)")
    # Also create PLINK format using pysam + PLINK
    return vcf_gz, samples, snps

# ---- 2. 表型文件 ----
def generate_pheno(samples):
    """Generate phenotype file (continuous + binary)."""
    pheno = pd.DataFrame({
        "FID": samples, "IID": samples,
        "PHENO": np.random.normal(170, 10, N_SAMPLES).round(2),  # height (cm)
    })
    pheno_path = os.path.join(OUT_DIR, "demo_pheno.txt")
    pheno.to_csv(pheno_path, sep="\t", index=False)
    print(f"Phenotype: {pheno_path} ({len(pheno)} samples)")
    # Binary phenotype
    pheno_bin = pheno.copy()
    median = pheno_bin["PHENO"].median()
    pheno_bin["PHENO"] = (pheno_bin["PHENO"] > median).astype(int) + 1  # 1=control, 2=case
    pheno_bin_path = os.path.join(OUT_DIR, "demo_pheno_binary.txt")
    pheno_bin.to_csv(pheno_bin_path, sep="\t", index=False)
    print(f"Binary phenotype: {pheno_bin_path}")
    return pheno_path, pheno_bin_path

# ---- 3. 协变量文件 ----
def generate_covar(samples):
    """Generate covariate file (age, sex, PC1-PC10)."""
    covar = pd.DataFrame({
        "FID": samples, "IID": samples,
        "age": np.random.randint(20, 80, N_SAMPLES),
        "sex": np.random.choice([1, 2], N_SAMPLES),
    })
    for i in range(1, 11):
        covar[f"PC{i}"] = np.random.normal(0, 0.1, N_SAMPLES).round(4)
    covar_path = os.path.join(OUT_DIR, "demo_covar.txt")
    covar.to_csv(covar_path, sep="\t", index=False)
    print(f"Covariates: {covar_path} ({len(covar)} samples)")
    return covar_path

# ---- 4. GWAS summary stats ----
def generate_sumstats(snps):
    """Generate mock GWAS summary statistics."""
    rows = []
    for chrom, pos, rsid, ref, alt in snps:
        beta = np.random.normal(0, 0.1)
        se = abs(np.random.normal(0.05, 0.02))
        # Some significant SNPs
        if random.random() < 0.02:
            beta = np.random.choice([-1, 1]) * np.random.uniform(0.3, 0.8)
            se = np.random.uniform(0.05, 0.1)
        from scipy.stats import norm
        z = beta / se
        p = 2 * norm.sf(abs(z))
        af = round(random.uniform(0.05, 0.5), 4)
        rows.append({
            "SNP": rsid, "CHR": chrom, "BP": pos,
            "A1": alt, "A2": ref, "BETA": round(beta, 4),
            "SE": round(se, 4), "P": f"{p:.4e}", "AF": af, "N": N_SAMPLES,
        })
    df = pd.DataFrame(rows)
    path = os.path.join(OUT_DIR, "demo_sumstats.txt")
    df.to_csv(path, sep="\t", index=False)
    n_sig = (df["P"].astype(float) < 5e-8).sum()
    print(f"GWAS sumstats: {path} ({len(df)} SNPs, {n_sig} significant)")
    return path

# ---- 5. eQTL summary stats ----
def generate_eqtl(snps):
    """Generate mock eQTL summary statistics."""
    rows = []
    gene_names = ["GENE" + str(i).zfill(3) for i in range(1, 51)]
    for chrom, pos, rsid, ref, alt in snps[:200]:
        gene = random.choice(gene_names)
        beta = np.random.normal(0, 0.2)
        se = abs(np.random.normal(0.1, 0.05))
        from scipy.stats import norm
        z = beta / se
        p = 2 * norm.sf(abs(z))
        rows.append({
            "SNP": rsid, "CHR": chrom, "BP": pos,
            "A1": alt, "A2": ref, "BETA": round(beta, 4),
            "SE": round(se, 4), "P": f"{p:.4e}", "GENE": gene, "N": 200,
        })
    df = pd.DataFrame(rows)
    path = os.path.join(OUT_DIR, "demo_eqtl.txt")
    df.to_csv(path, sep="\t", index=False)
    print(f"eQTL sumstats: {path} ({len(df)} SNPs)")
    return path

# ---- 6. 群体标签 ----
def generate_pop(samples):
    """Generate population labels."""
    pops = ["EAS"] * 25 + ["EUR"] * 15 + ["AFR"] * 10
    random.shuffle(pops)
    df = pd.DataFrame({"FID": samples, "IID": samples, "POP": pops})
    path = os.path.join(OUT_DIR, "demo_pop.txt")
    df.to_csv(path, sep="\t", index=False)
    print(f"Population: {path} ({df['POP'].value_counts().to_dict()})")
    return path

# ---- 7. 生成 PLINK 格式 ----
def generate_plink(vcf_gz):
    """Convert VCF to PLINK bed/bim/fam."""
    import shutil
    plink = shutil.which("plink") or os.path.expanduser("~/software/miniforge/envs/cima/bin/plink")
    if not plink:
        print("WARNING: PLINK not found, skipping PLINK format conversion")
        return None
    prefix = os.path.join(OUT_DIR, "demo_genotype")
    cmd = f"{plink} --vcf {vcf_gz} --make-bed --out {prefix} --allow-no-sex 2>/dev/null"
    os.system(cmd)
    if os.path.isfile(prefix + ".bed"):
        print(f"PLINK: {prefix}.bed/.bim/.fam")
        return prefix
    print("WARNING: PLINK conversion failed")
    return None

# ---- Main ----
if __name__ == "__main__":
    print(f"Generating demo data in {OUT_DIR}/...\n")
    vcf_gz, samples, snps = generate_vcf()
    generate_pheno(samples)
    generate_covar(samples)
    generate_sumstats(snps)
    generate_eqtl(snps)
    generate_pop(samples)
    generate_plink(vcf_gz)
    print(f"\nDone! All demo data in {OUT_DIR}/")
    print(f"\nTo test pipeline:")
    print(f"  cd {os.path.dirname(OUT_DIR)}")
    print(f"  python3 cohort_pipeline.py --list")
    print(f"  python3 cohort_pipeline.py --dry-run --config config.yaml")
