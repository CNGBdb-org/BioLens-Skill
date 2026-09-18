#!/usr/bin/env python3
"""
Cohort Pipeline — 统一主程序
================================
调度 18 个群体遗传学 skill 的 DAG 编排器。
支持：步骤选择、dry-run 预览、依赖检查、状态追踪。

用法:
  # 列出所有步骤
  python3 cohort_pipeline.py --list

  # dry-run 预览
  python3 cohort_pipeline.py --dry-run --config config.yaml

  # 从头运行全部
  python3 cohort_pipeline.py --config config.yaml

  # 只运行指定步骤
  python3 cohort_pipeline.py --config config.yaml --steps 1,2,4

  # 指定输入数据
  python3 cohort_pipeline.py --vcf input.vcf.gz --pheno pheno.txt --output results/

依赖: PLINK 1.9+, Python 3.10+, pandas, pysam
"""
import argparse
import os
import sys
import shutil
import subprocess
import json
import time
from pathlib import Path

# ============================================================
# Skill 定义：18 个步骤
# ============================================================
STEPS = [
    # --- 核心主干 ---
    {
        "num": 1, "name": "genotype_qc", "skill": "pop-genotype-qc",
        "desc": "基因型质控（missingness/HWE/MAF/杂合度/性别检查/亲缘关系）",
        "deps": [], "category": "核心主干",
        "script": "scripts/query.py",
        "cmd": "pipeline full --input {vcf} --output {output}/step01_qc",
        "inputs": ["vcf"], "outputs": ["step01_qc/variant_qc/filtered"],
    },
    {
        "num": 2, "name": "structure_pca", "skill": "pop-structure-pca",
        "desc": "群体结构分析（LD 剪枝/PCA/KMeans 聚类/离群检测/可视化）",
        "deps": [1], "category": "核心主干",
        "script": "scripts/query.py",
        "cmd": "pipeline full --input {qc_prefix} --output {output}/step02_pca",
        "inputs": ["qc_prefix"], "outputs": ["step02_pca/pca.eigenvec"],
    },
    {
        "num": 3, "name": "imputation", "skill": "pop-imputation",
        "desc": "基因型填充（前质控/Phasing/TOPMed-HRC 提交/后质控）",
        "deps": [1], "category": "核心主干",
        "script": "scripts/query.py",
        "cmd": "pipeline prepare --input {qc_prefix} --output {output}/step03_imputation",
        "inputs": ["qc_prefix"], "outputs": ["step03_imputation/submit"],
    },
    {
        "num": 4, "name": "gwas_association", "skill": "pop-gwas-association",
        "desc": "GWAS 关联分析（REGENIE/SAIGE/PLINK + λGC + Manhattan/QQ）",
        "deps": [1, 2], "category": "核心主干",
        "script": "scripts/query.py",
        "cmd": "pipeline full --input {qc_prefix} --pheno {pheno} --covar {covar} --output {output}/step04_gwas",
        "inputs": ["qc_prefix", "pheno", "covar"], "outputs": ["step04_gwas/gwas.assoc.linear"],
    },
    {
        "num": 5, "name": "variant_annotation", "skill": "pop-variant-annotation",
        "desc": "变异功能注释（VEP/ANNOVAR/SnpEff/bcftools/pysam）",
        "deps": [1], "category": "核心主干",
        "script": "scripts/query.py",
        "cmd": "pipeline full --input {vcf} --output {output}/step05_annotation",
        "inputs": ["vcf"], "outputs": ["step05_annotation"],
    },
    {
        "num": 6, "name": "prs", "skill": "pop-prs",
        "desc": "多基因风险评分（PLINK score/PRSice2/PRS-CS/LDpred2 + AUC/R2）",
        "deps": [4], "category": "核心主干",
        "script": "scripts/query.py",
        "cmd": "pipeline full --sumstats {sumstats} --target {qc_prefix} --pheno {pheno} --output {output}/step06_prs",
        "inputs": ["sumstats", "qc_prefix", "pheno"], "outputs": ["step06_prs/prs.profile"],
    },
    # --- 进阶分析 ---
    {
        "num": 7, "name": "finemapping", "skill": "pop-finemapping",
        "desc": "精细定位（SuSiE/FINEMAP/CAVIAR + PIP + credible set）",
        "deps": [4], "category": "进阶分析",
        "script": "scripts/query.py",
        "cmd": "pipeline full --sumstats {sumstats} --ld-ref {qc_prefix} --locus {locus} --output {output}/step07_finemap",
        "inputs": ["sumstats", "qc_prefix", "locus"], "outputs": ["step07_finemap/finemap_results.tsv"],
    },
    {
        "num": 8, "name": "colocalization", "skill": "pop-colocalization",
        "desc": "共定位分析（coloc.abf/eCAVIAR/HyPrColoc + PP4 + regional plot）",
        "deps": [4], "category": "进阶分析",
        "script": "scripts/query.py",
        "cmd": "pipeline full --gwas {sumstats} --qtl {eqtl} --locus {locus} --output {output}/step08_coloc",
        "inputs": ["sumstats", "eqtl", "locus"], "outputs": ["step08_coloc/coloc_result.json"],
    },
    {
        "num": 9, "name": "heritability_ldsc", "skill": "pop-heritability-ldsc",
        "desc": "遗传度估计（LDSC h2/分区富集/遗传相关 rg）",
        "deps": [4], "category": "进阶分析",
        "script": "scripts/query.py",
        "cmd": "pipeline full --sumstats {sumstats} --output {output}/step09_h2",
        "inputs": ["sumstats"], "outputs": ["step09_h2/h2_results.json"],
    },
    {
        "num": 10, "name": "pathway_enrichment", "skill": "pop-pathway-enrichment",
        "desc": "通路富集（MAGMA/GO/KEGG/Reactome + 组织特异性）",
        "deps": [4], "category": "进阶分析",
        "script": "scripts/query.py",
        "cmd": "pipeline full --sumstats {sumstats} --output {output}/step10_pathway",
        "inputs": ["sumstats"], "outputs": ["step10_pathway/gene_test/gene_results.txt"],
    },
    {
        "num": 11, "name": "mr_smr", "skill": "pop-mr-smr",
        "desc": "孟德尔随机化（SMR/TwoSampleMR/MR-PRESSO + IVW + MR-Egger）",
        "deps": [4, 8], "category": "进阶分析",
        "script": "scripts/query.py",
        "cmd": "pipeline full --exposure {eqtl} --outcome {sumstats} --output {output}/step11_mr",
        "inputs": ["eqtl", "sumstats"], "outputs": ["step11_mr/mr_results.json"],
    },
    {
        "num": 12, "name": "rare_variant_burden", "skill": "pop-rare-variant-burden",
        "desc": "罕见变异 burden 检验（SKAT-O/CMC + 基因聚合 + QQ plot）",
        "deps": [1, 5], "category": "进阶分析",
        "script": "scripts/query.py",
        "cmd": "pipeline full --vcf {vcf} --pheno {pheno} --output {output}/step12_burden",
        "inputs": ["vcf", "pheno"], "outputs": ["step12_burden/test/burden_results.tsv"],
    },
    # --- 扩展分析 ---
    {
        "num": 13, "name": "selection_scan", "skill": "pop-selection-scan",
        "desc": "选择信号检测（iHS/XP-EHH/Fst/PBS + Manhattan）",
        "deps": [1], "category": "扩展分析",
        "script": "scripts/query.py",
        "cmd": "pipeline full --input {qc_prefix} --pop {pop_file} --output {output}/step13_selection",
        "inputs": ["qc_prefix", "pop_file"], "outputs": ["step13_selection"],
    },
    {
        "num": 14, "name": "roh_inbreeding", "skill": "pop-roh-inbreeding",
        "desc": "ROH 纯合片段 + 近交系数（F(ROH)/Fhat + 分布图）",
        "deps": [1], "category": "扩展分析",
        "script": "scripts/query.py",
        "cmd": "pipeline full --input {qc_prefix} --output {output}/step14_roh",
        "inputs": ["qc_prefix"], "outputs": ["step14_roh/f_roh/f_roh.tsv"],
    },
    {
        "num": 15, "name": "ld_haplotype", "skill": "pop-ld-haplotype",
        "desc": "LD 分析（LD 衰减/矩阵/剪枝/单倍型频率 + 衰减曲线）",
        "deps": [1], "category": "扩展分析",
        "script": "scripts/query.py",
        "cmd": "pipeline full --input {qc_prefix} --output {output}/step15_ld",
        "inputs": ["qc_prefix"], "outputs": ["step15_ld/decay/ld_decay.tsv"],
    },
    {
        "num": 16, "name": "sv_cnv", "skill": "pop-sv-cnv",
        "desc": "结构变异与 CNV（DELLY/Manta + 频率 + 基因注释）",
        "deps": [], "category": "扩展分析",
        "script": "scripts/query.py",
        "cmd": "pipeline full --vcf {vcf} --output {output}/step16_sv",
        "inputs": ["vcf"], "outputs": ["step16_sv"],
    },
    {
        "num": 17, "name": "pharmacogenomics", "skill": "pop-pharmacogenomics",
        "desc": "药物基因组学（CYP2D6 等 6 基因 star allele + CPIC 剂量建议）",
        "deps": [], "category": "扩展分析",
        "script": "scripts/query.py",
        "cmd": "pipeline full --vcf {vcf} --output {output}/step17_pgx",
        "inputs": ["vcf"], "outputs": ["step17_pgx/pgx/pgx_summary.tsv"],
    },
    {
        "num": 18, "name": "gwas_visualization", "skill": "pop-gwas-visualization",
        "desc": "GWAS 综合可视化（Manhattan/QQ/Regional/Forest/Compare）",
        "deps": [4], "category": "扩展分析",
        "script": "scripts/query.py",
        "cmd": "pipeline full --sumstats {sumstats} --output {output}/step18_vis",
        "inputs": ["sumstats"], "outputs": ["step18_vis/manhattan.png"],
    },
]

SKILLS_DIR = os.path.dirname(os.path.abspath(__file__))


def find_plink():
    for name in ["plink2", "plink"]:
        p = shutil.which(name)
        if p: return p
        for d in [os.path.expanduser("~/software/miniforge/envs/cima/bin"),
                  os.path.expanduser("~/software/miniforge/bin")]:
            fp = os.path.join(d, name)
            if os.path.isfile(fp) and os.access(fp, os.X_OK): return fp
    return None


def check_dependencies(step, params):
    """Check if required inputs for a step are available."""
    missing = []
    for inp in step["inputs"]:
        val = params.get(inp)
        if val is None:
            missing.append(inp)
        elif isinstance(val, str) and not os.path.exists(val) and not val.startswith("step"):
            # Allow paths relative to output dir
            pass
    return missing


def run_step(step, params, dry_run=False):
    """Run a single pipeline step."""
    skill_dir = os.path.join(SKILLS_DIR, step["skill"])
    script = os.path.join(skill_dir, step["script"])

    if not os.path.isfile(script):
        print(f"ERROR: script not found: {script}")
        return False

    # Build command
    cmd_str = step["cmd"].format(**params)
    full_cmd = f"python3 {script} {cmd_str}"

    if dry_run:
        print(f"  [DRY-RUN] {full_cmd}")
        return True

    print(f"\n{'='*60}")
    print(f"Step {step['num']}: {step['name']} — {step['desc']}")
    print(f"Skill: {step['skill']}")
    print(f"Command: {full_cmd}")
    print(f"{'='*60}")

    try:
        r = subprocess.run(full_cmd, shell=True, capture_output=False, timeout=72000)
        return r.returncode == 0
    except subprocess.TimeoutExpired:
        print(f"ERROR: Step {step['num']} timed out")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def resolve_deps(step_nums, all_steps):
    """Resolve dependencies: given selected steps, add all required deps."""
    by_num = {s["num"]: s for s in all_steps}
    needed = set()
    queue = list(step_nums)
    while queue:
        n = queue.pop(0)
        if n in needed:
            continue
        needed.add(n)
        for dep in by_num[n]["deps"]:
            if dep not in needed:
                queue.append(dep)
    return sorted(needed)


def list_steps():
    """Print all available steps."""
    print(f"\n{'='*80}")
    print(f"Cohort Pipeline — 18 个群体遗传学分析步骤")
    print(f"{'='*80}\n")
    current_cat = ""
    for s in STEPS:
        if s["category"] != current_cat:
            current_cat = s["category"]
            print(f"\n--- {current_cat} ---")
        deps_str = f"deps: {s['deps']}" if s["deps"] else "deps: 无"
        print(f"  [{s['num']:2d}] {s['name']:25s} {s['desc']}")
        print(f"       skill: {s['skill']}, {deps_str}")
    print(f"\n总步骤数: {len(STEPS)}")
    print(f"\n用法:")
    print(f"  python3 cohort_pipeline.py --list")
    print(f"  python3 cohort_pipeline.py --dry-run --config config.yaml")
    print(f"  python3 cohort_pipeline.py --config config.yaml")
    print(f"  python3 cohort_pipeline.py --config config.yaml --steps 1,2,4")
    print(f"  python3 cohort_pipeline.py --vcf input.vcf.gz --pheno pheno.txt --output results/")


def generate_config(path):
    """Generate a template config file."""
    config = """# Cohort Pipeline 配置文件
# ================================

# 输入数据
vcf: data/demo_genotype.vcf.gz        # 输入 VCF 文件
pheno: data/demo_pheno.txt            # 表型文件（FID IID PHENO）
covar: data/demo_covar.txt            # 协变量文件（FID IID age sex PC1-PC10）
sumstats: data/demo_sumstats.txt      # GWAS summary statistics
eqtl: data/demo_eqtl.txt              # eQTL summary statistics
pop_file: data/demo_pop.txt           # 群体标签文件（FID IID POP）
locus: "1:1000000-2000000"            # 精细定位/共定位的目标 locus

# 输出
output: results                       # 输出目录

# 质控参数
maf: 0.05                             # MAF 下限
hwe: 1e-6                             # HWE p 值下限
sample_missing: 0.02                  # 样本缺失率上限
variant_missing: 0.02                 # 变异缺失率上限

# GWAS 参数
tool: plink                           # GWAS 工具（plink/regenie/saige/bolt）
binary: false                         # 是否二分类性状
pval_threshold: 5e-8                  # 显著性阈值

# PRS 参数
prs_method: plink                     # PRS 方法（plink/prsice2/prscs/ldpred2）
"""
    with open(path, "w") as f:
        f.write(config)
    print(f"Config template saved: {path}")


def load_config(path):
    """Load YAML config file."""
    import yaml
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(
        description="Cohort Pipeline — 18 个群体遗传学 skill 统一调度器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--list", action="store_true", help="列出所有步骤")
    parser.add_argument("--dry-run", action="store_true", help="预览执行计划但不运行")
    parser.add_argument("--config", help="配置文件 YAML")
    parser.add_argument("--steps", help="指定步骤（逗号分隔，如 1,2,4）")
    parser.add_argument("--vcf", help="输入 VCF 文件")
    parser.add_argument("--pheno", help="表型文件")
    parser.add_argument("--covar", help="协变量文件")
    parser.add_argument("--sumstats", help="GWAS summary stats")
    parser.add_argument("--eqtl", help="eQTL summary stats")
    parser.add_argument("--pop-file", help="群体标签文件")
    parser.add_argument("--locus", default="1:1000000-2000000", help="目标 locus")
    parser.add_argument("--output", default="results", help="输出目录")
    parser.add_argument("--generate-config", help="生成配置文件模板到指定路径")
    args = parser.parse_args()

    if args.list:
        list_steps()
        return

    if args.generate_config:
        generate_config(args.generate_config)
        return

    # Load config
    params = {
        "vcf": None, "pheno": None, "covar": None, "sumstats": None,
        "eqtl": None, "pop_file": None, "locus": args.locus,
        "output": args.output, "qc_prefix": None,
    }
    if args.config and os.path.isfile(args.config):
        cfg = load_config(args.config)
        params.update({k: v for k, v in cfg.items() if v})
    # CLI overrides
    for key in ["vcf", "pheno", "covar", "sumstats", "eqtl", "pop_file", "locus", "output"]:
        val = getattr(args, key.replace("-", "_"), None)
        if val:
            params[key] = val

    # Resolve qc_prefix from step 1 output
    params["qc_prefix"] = f"{params['output']}/step01_qc/variant_qc/filtered"

    # Determine steps to run
    if args.steps:
        step_nums = [int(s.strip()) for s in args.steps.split(",")]
        step_nums = resolve_deps(step_nums, STEPS)
    else:
        step_nums = list(range(1, 19))

    # Print execution plan
    print(f"\n{'='*60}")
    print(f"Cohort Pipeline Execution Plan")
    print(f"{'='*60}")
    print(f"Output: {params['output']}")
    print(f"Steps: {step_nums}")
    if args.dry_run:
        print("[DRY-RUN MODE]")

    # Check PLINK
    plink = find_plink()
    if plink:
        print(f"PLINK: {plink}")
    else:
        print("WARNING: PLINK not found. Steps 1-4, 13-15 will fail.")

    # Run steps
    completed = []
    failed = []
    for num in step_nums:
        step = next(s for s in STEPS if s["num"] == num)
        # Check deps
        missing_deps = [d for d in step["deps"] if d not in completed and d not in step_nums]
        if missing_deps and not args.dry_run:
            print(f"\nSKIP Step {num}: dependencies {missing_deps} not completed")
            failed.append(num)
            continue
        # Check inputs
        missing_inputs = check_dependencies(step, params)
        if missing_inputs and not args.dry_run:
            print(f"\nSKIP Step {num}: missing inputs {missing_inputs}")
            failed.append(num)
            continue
        # Run
        success = run_step(step, params, args.dry_run)
        if success:
            completed.append(num)
        else:
            failed.append(num)
            print(f"\nStep {num} FAILED. Continuing to next step...")

    # Summary
    print(f"\n{'='*60}")
    print(f"Pipeline Summary")
    print(f"{'='*60}")
    print(f"Completed: {completed}")
    print(f"Failed: {failed}")
    print(f"Output: {params['output']}")
    # Save status
    status = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "completed": completed, "failed": failed,
        "total_steps": len(step_nums), "output": params["output"],
    }
    status_path = os.path.join(params["output"], "pipeline_status.json")
    os.makedirs(params["output"], exist_ok=True)
    with open(status_path, "w") as f:
        json.dump(status, f, indent=2)
    print(f"Status saved: {status_path}")


if __name__ == "__main__":
    main()
