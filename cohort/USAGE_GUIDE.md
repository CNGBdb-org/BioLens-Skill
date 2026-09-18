# Cohort Skills 使用手册

> 18 个群体遗传学分析 Skill 的详细使用指南，含每个 skill 的提问示例。
> 直接在对话中复制示例即可触发对应 skill 分析。

---

## 目录

| # | Skill | 功能 | 页码 |
|---|-------|------|------|
| 1 | pop-genotype-qc | 基因型质控 | 第 2 节 |
| 2 | pop-structure-pca | 群体结构分析 | 第 3 节 |
| 3 | pop-imputation | 基因型填充 | 第 4 节 |
| 4 | pop-gwas-association | GWAS 关联分析 | 第 5 节 |
| 5 | pop-variant-annotation | 变异功能注释 | 第 6 节 |
| 6 | pop-prs | 多基因风险评分 | 第 7 节 |
| 7 | pop-finemapping | 精细定位 | 第 8 节 |
| 8 | pop-colocalization | 共定位分析 | 第 9 节 |
| 9 | pop-heritability-ldsc | 遗传度估计 | 第 10 节 |
| 10 | pop-pathway-enrichment | 通路富集 | 第 11 节 |
| 11 | pop-mr-smr | 孟德尔随机化 | 第 12 节 |
| 12 | pop-rare-variant-burden | 罕见变异 burden | 第 13 节 |
| 13 | pop-selection-scan | 选择信号检测 | 第 14 节 |
| 14 | pop-roh-inbreeding | ROH 与近交 | 第 15 节 |
| 15 | pop-ld-haplotype | LD 与单倍型 | 第 16 节 |
| 16 | pop-sv-cnv | 结构变异与 CNV | 第 17 节 |
| 17 | pop-pharmacogenomics | 药物基因组学 | 第 18 节 |
| 18 | pop-gwas-visualization | GWAS 可视化 | 第 19 节 |

---

## 1. 快速开始

### 通过对话使用

直接在对话框中输入你的问题或需求，我会自动匹配到对应 skill 并执行。也可以先说「我要使用群体遗传学技能库」来激活。

### 通过命令行使用

```bash
cd skills/cohort
python3 cohort_pipeline.py --list                    # 查看所有步骤
python3 cohort_pipeline.py --dry-run --config config.yaml  # 预览
python3 cohort_pipeline.py --config config.yaml      # 运行全部
python3 cohort_pipeline.py --config config.yaml --steps 1,2,4  # 指定步骤
```

### Demo 数据

```bash
python3 generate_demo_data.py  # 生成 50 样本 × 484 SNP 的测试数据
```

---

## 2. pop-genotype-qc — 基因型质控

**功能：** 对 VCF 或 PLINK 格式的基因型数据做 GWAS 前质控，包括样本缺失率、变异缺失率、HWE、MAF、杂合度离群、性别检查和亲缘关系检测。

**输入：** VCF(.gz) 或 PLINK bed/bim/fam 前缀
**输出：** cleaned genotype + QC 报告

### 提问示例

1. "我有一个群体的 VCF 文件在 /path/to/cohort.vcf.gz，帮我做 GWAS 前质控"
2. "检查一下这个 PLINK 数据的样本杂合度有没有离群，输入前缀是 /path/to/cohort"
3. "帮我检测这个群体里有没有重复样本和亲缘关系，数据在 /path/to/cohort"

---

## 3. pop-structure-pca — 群体结构分析

**功能：** LD 剪枝 + PCA + KMeans 聚类 + PC 离群检测 + 散点图可视化。

**输入：** QC 后的 PLINK 前缀
**输出：** eigenvalues, eigenvectors, cluster labels, PCA scatter plot

### 提问示例

1. "帮我做 PCA 分析群体结构，数据在 /path/to/qc_filtered"
2. "这个群体有没有分层？帮我聚类看看有几个人群，PLINK 前缀是 /path/to/cohort"
3. "帮我检测 PCA 离群样本并画 PC1 vs PC2 散点图，输入 /path/to/cohort"

---

## 4. pop-imputation — 基因型填充

**功能：** 填充前质控（等位基因/链方向检查）+ Phasing 准备（Eagle/SHAPEIT4）+ TOPMed/HRC 提交文件 + 填充后质控（info score 过滤、AF 一致性）。

**输入：** QC 后的 PLINK 前缀
**输出：** 提交 VCF + 样本元数据 + 填充后 SNP 列表

### 提问示例

1. "我的基因芯片数据需要做填充，帮我准备 TOPMed 提交文件，PLINK 前缀 /path/to/cohort"
2. "填充结果回来了，帮我做后质控，info score 阈值 0.3，数据在 /path/to/imputed/"
3. "检查一下填充前后等位基因频率一致性，原始数据 /path/to/cohort，填充结果 /path/to/imputed/"

---

## 5. pop-gwas-association — GWAS 关联分析

**功能：** 支持 PLINK/REGENIE/SAIGE/BOLT-LMM 关联分析 + λGC 计算 + Manhattan/QQ plot。连续型和二分类性状均可。

**输入：** PLINK 前缀 + 表型文件 + 协变量文件
**输出：** summary statistics + Manhattan + QQ + λGC

### 提问示例

1. "帮我跑 GWAS 关联分析，基因型 /path/to/cohort，表型 /path/to/pheno.txt，协变量 /path/to/covar.txt，用 PLINK"
2. "用 REGENIE 跑二分类 GWAS，病例对照数据，输入 /path/to/cohort"
3. "我的 GWAS 结果膨胀了吗？帮我算 λGC，sumstats 在 /path/to/gwas_results.txt"

---

## 6. pop-variant-annotation — 变异功能注释

**功能：** 自动检测 VEP/SnpEff/bcftools/ANNOVAR，对 VCF 或变异列表做功能注释。无外部工具时用 pysam 做基础注释。

**输入：** VCF 文件或变异列表
**输出：** annotated VCF/TSV + 变异类型统计

### 提问示例

1. "帮我注释这个 VCF 里的变异功能，文件在 /path/to/variants.vcf.gz"
2. "GWAS 显著的 SNP 列表帮我注释一下，看看是 missense 还是 synonymous，列表在 /path/to/significant_snps.txt"
3. "用 pysam 快速统计一下这个 VCF 有多少 SNV、多少 INDEL，文件 /path/to/cohort.vcf.gz"

---

## 7. pop-prs — 多基因风险评分

**功能：** 从 GWAS summary stats 计算目标群体的 PRS，支持 PLINK score/PRSice2/PRS-CS/LDpred2。含 clumping、AUC/R2 评估和分布图。

**输入：** GWAS sumstats + 目标基因型 + 表型（评估用）
**输出：** per-individual PRS + AUC/R2 + 分布图

### 提问示例

1. "帮我用这个 GWAS sumstats 计算目标群体的 PRS，sumstats /path/to/sumstats.txt，目标基因型 /path/to/cohort"
2. "PRS 算完了帮我评估一下预测效果，算 AUC，评分文件 /path/to/prs.profile，表型 /path/to/pheno_binary.txt"
3. "用 PRSice2 多阈值扫描做 PRS，比较不同 p 值阈值的预测效果"

---

## 8. pop-finemapping — 精细定位

**功能：** SuSiE/FINEMAP/CAVIAR 精细定位，计算 PIP、构建 95% credible set、LocusZoom 可视化。

**输入：** GWAS sumstats + LD 参考面板 + locus 范围
**输出：** PIP 排序表 + credible set + LocusZoom plot

### 提问示例

1. "帮我做精细定位，sumstats /path/to/gwas.txt，LD 参考 /path/to/cohort，locus chr1:1000000-2000000"
2. "用 SuSiE 精细定位这个位点，看看 95% credible set 里有哪些候选因果变异"
3. "帮我画 LocusZoom 图，把 PIP 标在关联信号上"

---

## 9. pop-colocalization — 共定位分析

**功能：** 检验 GWAS 与 eQTL/caQTL 是否共享因果变异，支持 coloc.abf/eCAVIAR/HyPrColoc，输出 PP4 和 regional plot。

**输入：** GWAS sumstats + QTL sumstats + locus 范围
**输出：** PP4 + 5 假设后验概率 + regional plot

### 提问示例

1. "帮我检验 GWAS 和 eQTL 是否共定位，GWAS /path/to/gwas.txt，eQTL /path/to/eqtl.txt，locus chr1:1000000-2000000"
2. "这个位点的 GWAS 信号和 eQTL 是同一个因果变异吗？帮我算 PP4"
3. "帮我画 regional plot，上下两面板分别显示 GWAS 和 eQTL 的关联信号"

---

## 10. pop-heritability-ldsc — 遗传度估计

**功能：** LDSC 估计 SNP 遗传度(h2)、分区富集和双性状遗传相关(rg)。未安装 LDSC 时用 Python 近似。

**输入：** GWAS sumstats（需 munge 后）
**输出：** h2 + intercept + 分区富集表 + rg

### 提问示例

1. "帮我估计这个性状的 SNP 遗传度，sumstats /path/to/gwas.txt"
2. "这两个性状之间的遗传相关是多少？sumstats1 /path/to/trait1.txt，sumstats2 /path/to/trait2.txt"
3. "帮我做分区遗传度分析，看看哪些功能注释富集遗传信号"

---

## 11. pop-pathway-enrichment — 通路富集

**功能：** MAGMA 基因水平关联 + GO/KEGG/Reactome 通路富集 + 组织特异性富集。未安装 MAGMA 时用 Python Fisher 合并。

**输入：** GWAS sumstats
**输出：** 基因 p-value + 通路富集表 + 组织富集表

### 提问示例

1. "帮我做通路富集分析，看看 GWAS 信号富集在哪些生物学通路，sumstats /path/to/gwas.txt"
2. "做基因水平关联，把 SNP p-value 聚合到基因，sumstats /path/to/gwas.txt"
3. "GWAS 信号在哪些组织特异性富集？用 GTEx 表达数据，表达矩阵 /path/to/gtex_expr.txt"

---

## 12. pop-mr-smr — 孟德尔随机化

**功能：** SMR/TwoSampleMR/MR-PRESSO 因果推断，含 IVW/MR-Egger/weighted median 和 HEIDI 检验。未安装时用 Python IVW 近似。

**输入：** 暴露 sumstats(eQTL) + 结局 sumstats(GWAS disease)
**输出：** 因果效应估计 + HEIDI p + MR-Egger intercept

### 提问示例

1. "帮我检验基因表达对疾病的因果效应，eQTL /path/to/eqtl.txt，GWAS /path/to/gwas.txt"
2. "用 SMR 做孟德尔随机化，看看 IKZF4 表达和哮喘有没有因果关联"
3. "帮我做多效性检测，看看 MR-Egger intercept 是否显著"

---

## 13. pop-selection-scan — 选择信号检测

**功能：** iHS（近期选择）/ XP-EHH（跨群体固定选择）/ Fst（群体分化）/ PBS（三群体分支统计）。selscan 未安装时 Fst 仍可用。

**输入：** PLINK 前缀 + 群体标签文件
**输出：** 标准化 iHS/XP-EHH + Fst + PBS + Manhattan plot

### 提问示例

1. "帮我检测这个群体的选择信号，PLINK /path/to/cohort，群体标签 /path/to/pop.txt"
2. "比较东亚和欧洲群体的 Fst，看看哪些区域分化最大"
3. "用三个群体算 PBS，看看哪个群体有特异性选择信号"

---

## 14. pop-roh-inbreeding — ROH 与近交系数

**功能：** PLINK --homozyg 检测 ROH + F(ROH) 近交系数 + Fhat 统计 + ROH 长度分布图。

**输入：** PLINK 前缀
**输出：** per-individual ROH + F(ROH) + Fhat + 分布图

### 提问示例

1. "帮我检测 ROH 纯合片段并计算近交系数，PLINK /path/to/cohort"
2. "这个群体里有没有高近交个体？帮我画 F(ROH) 分布图"
3. "ROH 按长度分类，短 ROH（远期共祖）和长 ROH（近期共祖）各有多少？"

---

## 15. pop-ld-haplotype — LD 与单倍型

**功能：** LD 衰减分析（r2 vs 距离）+ LD 矩阵（指定区域）+ LD 剪枝 + 单倍型频率 + 衰减曲线图。

**输入：** PLINK 前缀
**输出：** LD 衰减表 + LD 矩阵 + 独立 SNP 列表 + 衰减曲线

### 提问示例

1. "帮我做 LD 衰减分析，看看 r2 随距离怎么变化，PLINK /path/to/cohort"
2. "生成 chr1:1000000-2000000 区域的 LD 矩阵，用于精细定位"
3. "帮我做 LD 剪枝获取独立 SNP，r2 阈值 0.2，窗口 50kb"

---

## 16. pop-sv-cnv — 结构变异与 CNV

**功能：** DELLY/Manta SV 检测 + pysam VCF 解析 + CNV 频率统计 + 基因重叠注释。

**输入：** VCF 或 BAM list
**输出：** SV calls + 频率表 + 基因注释

### 提问示例

1. "帮我解析这个 SV VCF 文件，统计各种 SV 类型和频率，文件 /path/to/sv_calls.vcf.gz"
2. "这些结构变异有没有影响基因？帮我做基因重叠注释"
3. "帮我统计 CNV 在群体中的携带频率，VCF /path/to/cnv.vcf.gz"

---

## 17. pop-pharmacogenomics — 药物基因组学

**功能：** CYP2D6/CYP2C19/CYP2C9/CYP3A5/SLCO1B1/TPMT 六个基因 star allele 分型 + 代谢表型预测（PM/IM/NM/RM/UM）+ CPIC 剂量建议。

**输入：** VCF 文件
**输出：** per-individual PGx 报告 + 群体频率表 + 剂量建议

### 提问示例

1. "帮我做药物基因组学分型，看看这个群体的 CYP2D6 和 CYP2C19 代谢表型，VCF /path/to/cohort.vcf.gz"
2. "可待因的剂量建议是什么？根据 CYP2D6 基因型给出用药指导"
3. "帮我统计这个群体中慢代谢者(PM)的比例，VCF /path/to/cohort.vcf.gz"

---

## 18. pop-gwas-visualization — GWAS 可视化

**功能：** Manhattan plot + QQ plot + Regional association plot + Forest plot + 双性状 Manhattan 对比 + Summary 表。自动检测列名，支持高亮 SNP。

**输入：** GWAS summary stats
**输出：** Manhattan/QQ/Regional/Forest/Compare PNG + summary TSV

### 提问示例

1. "帮我画 Manhattan plot 和 QQ plot，sumstats /path/to/gwas.txt"
2. "帮我画 chr1:1000000-2000000 的 regional association plot"
3. "对比两个性状的 GWAS 结果，画上下双面板 Manhattan，sumstats1 /path/to/trait1.txt，sumstats2 /path/to/trait2.txt"

---

## 附录 A：典型分析流程

### GWAS 标准流程（质控 → GWAS → 注释 → 可视化）

```
1. 质控:     pop-genotype-qc       "帮我做 GWAS 前质控"
2. PCA:      pop-structure-pca      "做 PCA 看群体结构"
3. GWAS:     pop-gwas-association   "跑 GWAS 关联分析"
4. 注释:     pop-variant-annotation "注释显著变异功能"
5. 可视化:   pop-gwas-visualization "画 Manhattan 和 QQ"
```

### 因果推断流程（GWAS → 精细定位 → 共定位 → MR）

```
7. 精细定位:  pop-finemapping       "做精细定位"
8. 共定位:    pop-colocalization    "GWAS 和 eQTL 共定位"
11. MR:       pop-mr-smr            "孟德尔随机化"
```

### 群体特征流程（ROH → 选择信号 → LD → PGx）

```
14. ROH:      pop-roh-inbreeding    "检测 ROH 和近交"
13. 选择:     pop-selection-scan    "检测选择信号"
15. LD:       pop-ld-haplotype      "LD 衰减分析"
17. PGx:      pop-pharmacogenomics  "药物基因组学分型"
```

## 附录 B：Demo 数据说明

| 文件 | 内容 | 大小 |
|------|------|------|
| data/demo_genotype.vcf.gz | 50 样本 × 484 SNP VCF | ~19KB |
| data/demo_genotype.bed/.bim/.fam | PLINK 格式 | ~21KB |
| data/demo_pheno.txt | 连续表型（身高 cm） | ~1.5KB |
| data/demo_pheno_binary.txt | 二分类表型（1=对照, 2=病例） | ~1.2KB |
| data/demo_covar.txt | 协变量（age/sex/PC1-10） | ~5KB |
| data/demo_sumstats.txt | GWAS summary stats（484 SNP, 38 显著） | ~30KB |
| data/demo_eqtl.txt | eQTL summary stats（200 SNP × 50 基因） | ~13KB |
| data/demo_pop.txt | 群体标签（EAS 25/EUR 15/AFR 10） | ~1.3KB |

## 附录 C：依赖工具一览

### 核心依赖（已有）

Python 3.10+, PLINK 1.9, pysam, pandas, numpy, scipy, matplotlib, sklearn

### 可选依赖（按需安装）

| 工具 | 安装命令 | 用于 |
|------|---------|------|
| REGENIE | conda install -c bioconda regenie | GWAS (#4) |
| VEP | conda install -c bioconda ensembl-vep | 注释 (#5) |
| SnpEff | conda install -c bioconda snpeff | 注释 (#5) |
| bcftools | conda install -c bioconda htslib | 注释 (#5) / SV (#16) |
| Eagle | conda install -c bioconda eagle | 填充 (#3) |
| PRSice2 | https://www.prsice.info/ | PRS (#6) |
| R + susieR | conda install -c conda-forge r-susier | 精细定位 (#7) |
| R + coloc | conda install -c bioconda r-coloc | 共定位 (#8) |
| LDSC | conda install -c bioconda ldsc | 遗传度 (#9) |
| MAGMA | https://ctg.cncr.nl/software/magma | 通路 (#10) |
| SMR | http://yanglab.westlake.edu.cn/software/smr/ | MR (#11) |
| R + SKAT | conda install -c bioconda r-skat | 罕见变异 (#12) |
| selscan | conda install -c bioconda selscan | 选择信号 (#13) |
| DELLY | conda install -c bioconda delly | SV (#16) |
