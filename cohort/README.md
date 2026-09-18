# Cohort Skills — 大规模人群队列遗传学分析技能集

> 18 个覆盖从 VCF 到因果推断的完整群体遗传学分析 Skill。
> 每个 Skill 自包含：SKILL.md（使用说明）+ scripts/query.py（可执行脚本）。

路径：`skills/cohort/<name>/`。Agent 部署用 `./skills/install-to-agent.sh --agent cursor --category cohort`。

**与公开库 Skill 分工（勿重叠）：**

| 需求 | 用 |
|------|-----|
| 已发表 GWAS Catalog 关联 | `gwascatalog` |
| PharmGKB / CPIC 指南 API | `pharmgkb` |
| CIMA 预计算免疫病 SMR 表 | `cima-smr-gwas` |
| ClinVar / dbSNP / gnomAD 查询 | `clinvar` / `dbsnp` / `gnomad` |
| GO/KEGG **术语**查询 | `go` / `kegg` |
| 本地队列 VCF/PLINK 分析 | 本目录 `pop-*` |


## 目录

| 批次 | # | Skill | 功能 |
|------|---|-------|------|
| 核心主干 | 1 | pop-genotype-qc | 基因型质控（missingness/HWE/MAF/杂合度/性别检查/亲缘关系） |
| 核心主干 | 2 | pop-structure-pca | 群体结构分析（LD 剪枝/PCA/KMeans 聚类/离群检测/可视化） |
| 核心主干 | 3 | pop-imputation | 基因型填充（前质控/Phasing/TOPMed-HRC 提交/后质控） |
| 核心主干 | 4 | pop-gwas-association | GWAS 关联分析（REGENIE/SAIGE/BOLT-LMM/PLINK + Manhattan/QQ） |
| 核心主干 | 5 | pop-variant-annotation | 变异功能注释（VEP/ANNOVAR/SnpEff/bcftools/pysam） |
| 核心主干 | 6 | pop-prs | 多基因风险评分（PLINK score/PRSice2/PRS-CS/LDpred2 + AUC/R2） |
| 进阶分析 | 7 | pop-finemapping | 精细定位（SuSiE/FINEMAP/CAVIAR + PIP + credible set） |
| 进阶分析 | 8 | pop-colocalization | 共定位分析（coloc.abf/eCAVIAR/HyPrColoc + PP4） |
| 进阶分析 | 9 | pop-heritability-ldsc | 遗传度估计（LDSC h2/分区富集/遗传相关 rg） |
| 进阶分析 | 10 | pop-pathway-enrichment | 通路富集（MAGMA/GO/KEGG/Reactome + 组织特异性） |
| 进阶分析 | 11 | pop-mr-smr | 孟德尔随机化（SMR/TwoSampleMR/MR-PRESSO + IVW） |
| 进阶分析 | 12 | pop-rare-variant-burden | 罕见变异 burden 检验（SKAT-O/CMC + 基因聚合） |
| 扩展分析 | 13 | pop-selection-scan | 选择信号检测（iHS/XP-EHH/Fst/PBS） |
| 扩展分析 | 14 | pop-roh-inbreeding | ROH 纯合片段 + 近交系数（F(ROH)/Fhat） |
| 扩展分析 | 15 | pop-ld-haplotype | LD 分析（LD 衰减/矩阵/剪枝/单倍型频率） |
| 扩展分析 | 16 | pop-sv-cnv | 结构变异与 CNV（DELLY/Manta + 频率 + 基因注释） |
| 扩展分析 | 17 | pop-pharmacogenomics | 药物基因组学（CYP2D6 等 6 基因 star allele + CPIC 剂量） |
| 扩展分析 | 18 | pop-gwas-visualization | GWAS 综合可视化（Manhattan/QQ/Regional/Forest/Compare） |

## 分析流程图

```
VCF
 |
[1] pop-genotype-qc        样本/变异质控
 |
 ├──[2] pop-structure-pca    群体结构 PCA
 |
 ├──[3] pop-imputation       基因型填充
 |    |
 |    └──[4] pop-gwas-association  GWAS 关联分析
 |         |
 |         ├──[5] pop-variant-annotation  变异功能注释
 |         |
 |         ├──[6] pop-prs                 多基因风险评分
 |         |
 |         ├──[7] pop-finemapping         精细定位
 |         |
 |         ├──[8] pop-colocalization      共定位分析
 |         |
 |         ├──[9] pop-heritability-ldsc   遗传度估计
 |         |
 |         ├──[10] pop-pathway-enrichment 通路富集
 |         |
 |         ├──[11] pop-mr-smr             孟德尔随机化
 |         |
 |         └──[18] pop-gwas-visualization  综合可视化
 |
 ├──[12] pop-rare-variant-burden  罕见变异 burden
 |
 ├──[13] pop-selection-scan       选择信号
 ├──[14] pop-roh-inbreeding      ROH + 近交
 ├──[15] pop-ld-haplotype        LD + 单倍型
 ├──[16] pop-sv-cnv              结构变异 + CNV
 └──[17] pop-pharmacogenomics    药物基因组学
```

## 依赖环境

### 核心依赖（已有）

| 工具 | 版本 | 用途 |
|------|------|------|
| Python 3 | 3.10+ | 所有脚本 |
| PLINK | 1.9 | 基因型质控/PCA/GWAS/ROH/LD/Fst |
| pysam | 0.24+ | VCF 解析/变异注释/SV 检测 |
| pandas | 2.x | 数据处理 |
| numpy | 2.x | 数值计算 |
| scipy | 1.18+ | 统计检验 |
| matplotlib | 3.x | 可视化 |
| sklearn | 1.x+ | 聚类/AUC |

### 可选依赖（按需安装）

| 工具 | 安装命令 | 用于 Skill |
|------|---------|-----------|
| REGENIE | conda install -c bioconda regenie | #4 GWAS |
| SAIGE | conda install -c bioconda saige | #4 GWAS |
| VEP | conda install -c bioconda ensembl-vep | #5 注释 |
| SnpEff | conda install -c bioconda snpeff | #5 注释 |
| bcftools | conda install -c bioconda bcftools | #5 注释 / #16 SV |
| Eagle | conda install -c bioconda eagle | #3 填充 |
| SHAPEIT4 | conda install -c bioconda shapeit4 | #3 填充 |
| PRSice2 | https://www.prsice.info/ | #6 PRS |
| R + susieR | conda install -c conda-forge r-susier | #7 精细定位 |
| R + coloc | conda install -c bioconda r-coloc | #8 共定位 |
| LDSC | conda install -c bioconda ldsc | #9 遗传度 |
| MAGMA | https://ctg.cncr.nl/software/magma | #10 通路 |
| SMR | http://yanglab.westlake.edu.cn/software/smr/ | #11 MR |
| R + SKAT | conda install -c bioconda r-skat | #12 罕见变异 |
| selscan | conda install -c bioconda selscan | #13 选择信号 |
| DELLY | conda install -c bioconda delly | #16 SV |
| Manta | conda install -c bioconda manta | #16 SV |

## 使用方式

### 单个 Skill 运行

```bash
cd skills/cohort/<skill-name>
python3 ./scripts/query.py --help
python3 ./scripts/query.py pipeline full --input <your_data> --output <output_dir>
```

### 18 步编排（可选）

```bash
cd skills/cohort
python3 cohort_pipeline.py --list
python3 cohort_pipeline.py --dry-run --config config.yaml
# 从仓库根目录安装本分类：
# ./skills/install-to-agent.sh --agent cursor --category cohort
```

工作目录在 `skills/cohort/` 时，下面场景中的 `cd pop-*` 相对路径有效。

### 与 DCS Genpilot 对话使用

直接用自然语言描述需求，我会自动加载对应 skill：

- "帮我做 GWAS 前质控" → pop-genotype-qc
- "算一下 PRS" → pop-prs
- "做精细定位" → pop-finemapping
- "看看药物基因组学分型" → pop-pharmacogenomics

## 典型分析场景

### 场景一：GWAS 标准流程（VCF → 显著位点）

```bash
# 1. 质控
cd pop-genotype-qc
python3 scripts/query.py pipeline full --input cohort.vcf.gz --output qc_results

# 2. 群体结构
cd ../pop-structure-pca
python3 scripts/query.py pipeline full --input qc_results/variant_qc/filtered --output pca_results

# 3. GWAS 关联
cd ../pop-gwas-association
python3 scripts/query.py pipeline full --input qc_results/variant_qc/filtered --pheno phenotype.txt --covar covariates.txt --output gwas_results

# 4. 变异注释
cd ../pop-variant-annotation
python3 scripts/query.py pipeline full --input significant_variants.vcf --output annot_results

# 5. 可视化
cd ../pop-gwas-visualization
python3 scripts/query.py pipeline full --sumstats gwas_results/gwas.assoc.linear --output plots
```

### 场景二：因果推断（GWAS → 基因 → 疾病）

```bash
# 1. 精细定位
cd pop-finemapping
python3 scripts/query.py pipeline full --sumstats gwas.txt --ld-ref reference_panel --locus chr1:1000000-2000000 --output finemap

# 2. 共定位（GWAS × eQTL）
cd ../pop-colocalization
python3 scripts/query.py pipeline full --gwas gwas.txt --qtl eqtl.txt --locus chr1:1000000-2000000 --output coloc

# 3. 孟德尔随机化
cd ../pop-mr-smr
python3 scripts/query.py pipeline full --exposure eqtl.txt --outcome gwas.txt --output mr_results
```

### 场景三：群体特征分析

```bash
# 1. ROH + 近交
cd pop-roh-inbreeding
python3 scripts/query.py pipeline full --input qc_prefix --output roh_results

# 2. 选择信号
cd ../pop-selection-scan
python3 scripts/query.py run fst --input qc_prefix --pop population.txt --output fst_results

# 3. LD 衰减
cd ../pop-ld-haplotype
python3 scripts/query.py pipeline full --input qc_prefix --output ld_results

# 4. 药物基因组学
cd ../pop-pharmacogenomics
python3 scripts/query.py pipeline full --vcf cohort.vcf.gz --output pgx_results
```

## 设计原则

1. **工具自动检测**：所有脚本自动检测可用工具路径，未安装时回退 Python 近似并给出安装命令
2. **标准化格式**：输入接受 VCF / PLINK bed/bim/fam / GWAS sumstats，输出为 TSV + JSON + PNG
3. **参数化**：默认值参考 UK Biobank / CIMA 等大规模队列标准，可按需调整
4. **渐进式披露**：SKILL.md 描述使用场景和命令，references/ 放详细参数文档
5. **可复现**：输出包含 provenance（输入文件、参数、工具版本、时间戳）

## 作者

cngbdb-skill-team

## 引用

详见各 SKILL.md 末尾的 Citation 部分。
