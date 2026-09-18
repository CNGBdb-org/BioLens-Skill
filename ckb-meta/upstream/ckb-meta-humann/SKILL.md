---
name: ckb-meta-humann
description: >-
  Functional annotation of metagenomics samples using HUMAnN3. Takes rmhost
  FASTQ (paired-end or single-end) from ckb-meta-qc, runs MetaPhlAn4 internally
  then HUMAnN3 for gene families, pathway abundance, and pathway coverage.
  Outputs per-sample functional tables for ckb-meta-merge and ckb-meta-functional.
  Use when functional profiling (KO/GO/Pfam/pathways) of gut microbiome is needed.
  Not for taxonomy-only profiling (use ckb-meta-taxonomy alone for speed).
compatibility: "HUMAnN3 ≥3.9; MetaPhlAn4 ≥4.1; bowtie2 ≥2.4.5; diamond ≥2.1; Python 3.10+; Linux x86_64; ≥32 GB RAM"
metadata:
  author: ckb-meta-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: metagenomics
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# ckb-meta-humann：HUMAnN3 功能注释

## Use When
- 需要功能注释（基因家族、通路丰度、KO/GO/Pfam regroup）
- 输入来自 ckb-meta-qc 的 rmhost FASTQ

## Do Not Use When
| 需求 | 交给 |
|---|---|
| 只需物种 profile（速度优先）| ckb-meta-taxonomy |
| 已有功能矩阵需合并 | ckb-meta-merge |
| 功能差异统计 | ckb-meta-functional |

## 软件依赖

```bash
# HUMAnN3（biobakery 环境）
which humann && humann --version
# 要求：HUMAnN >= 3.9
# 安装：conda create -n biobakery3 -c biobakery humann=3.9
#       conda activate biobakery3

# MetaPhlAn4（HUMAnN 内部依赖，biobakery3 环境中已含）
which metaphlan && metaphlan --version
# 要求：>= 4.1.0

# DIAMOND（HUMAnN 蛋白比对依赖）
which diamond && diamond --version
# 要求：>= 2.1.0
```

## 数据库依赖

| 数据库 | 版本 | 大小 | DCS 路径 | 官方下载 |
|---|---|---|---|---|
| MetaPhlAn4 SGB 数据库 | mpa_vOct22_CHOCOPhlAnSGB_202212 | ~46 GB | `/public/database/CKB_metagenome/metaphlan/` | `metaphlan --install` |
| HUMAnN ChocoPhlAn | v201901 | ~3 GB（解压前 ~3 GB tar.gz）| `/public/database/CKB_metagenome/humann3/chocophlan1/` | `humann_databases --download chocophlan full /path/to/db` |
| HUMAnN UniRef90 | v201901b | ~20 GB（.dmnd）| `/public/database/CKB_metagenome/humann3/uniref90_201901/` | `humann_databases --download uniref uniref90_diamond /path/to/db` |
| HUMAnN utility mapping | v201901b | ~2.6 GB | `/public/database/CKB_metagenome/humann3/full_mapping_v201901b/` | `humann_databases --download utility_mapping full /path/to/db` |

非 DCS 环境下载（需约 ~72 GB 磁盘空间）：
```bash
conda activate biobakery3
# 下载所有 HUMAnN 数据库（约 1~3 小时）
humann_databases --download chocophlan full /path/to/humann_db
humann_databases --download uniref uniref90_diamond /path/to/humann_db
humann_databases --download utility_mapping full /path/to/humann_db
# 配置 HUMAnN 数据库路径
humann_config --update database_folders nucleotide /path/to/humann_db/chocophlan
humann_config --update database_folders protein /path/to/humann_db/uniref
humann_config --update database_folders utility_mapping /path/to/humann_db/utility_mapping
```

## Required Inputs

| 参数 | 说明 |
|---|---|
| rmhost1 | rmhost R1 FASTQ.gz（双端）或单端 FASTQ.gz |
| rmhost2 | rmhost R2 FASTQ.gz（双端，PE 模式下必填）|
| sampleid | 样本 ID |
| bowtie2db | MetaPhlAn Bowtie2 数据库目录 |
| humann_nucleotide_db | ChocoPhlAn 目录 |
| humann_protein_db | UniRef90 目录 |
| humann_utility_mapping_db | mapping 目录 |

## Necessary Questions

1. 双端（PE）还是单端（SE）数据？→ 决定使用 PE 还是 SE 路径
2. 用户未提供数据库路径时 → 说明四个数据库的位置和大小，停止

## Workflow

**Gather**：确认 FASTQ、4 个数据库路径

**Act**（以 PE 为例）：
```bash
# 合并双端 reads
cat {rmhost1} {rmhost2} > {sampleid}.combined.fq.gz

# HUMAnN3 主流程
humann \
  --input {sampleid}.combined.fq.gz \
  --output {sampleid}_humann3 \
  --threads 16 \
  --metaphlan-options "--bowtie2db {bowtie2db} --index mpa_vOct22_CHOCOPhlAnSGB_202212" \
  --nucleotide-database {humann_nucleotide_db} \
  --protein-database {humann_protein_db}

# regroup 到 KO/GO/Pfam
humann_regroup_table -i {sampleid}_humann3/{sampleid}_genefamilies.tsv \
  -g uniref90_ko -o {sampleid}_uniref90_ko_groupped.tsv
```

**DCS 平台（PE）**：投递 `rmhost_humann_PE`；**SE**：投递 `rmhost_humann_SE`

**Verify**：`wc -l {sampleid}_humann3/{sampleid}_pathabundance.tsv`

## Output Contract

| 文件 | 说明 | 下游 |
|---|---|---|
| `{sampleid}_genefamilies.tsv` | UniRef90 基因家族丰度 | ckb-meta-merge |
| `{sampleid}_pathabundance.tsv` | MetaCyc 通路丰度 | ckb-meta-merge → ckb-meta-functional |
| `{sampleid}_pathcoverage.tsv` | 通路覆盖度 | - |
| `{sampleid}_uniref90_ko_groupped.tsv` | KO regroup | ckb-meta-functional |
| `{sampleid}_uniref90_go_groupped.tsv` | GO regroup | ckb-meta-functional |

## Guardrails

- 双端数据必须合并后传入 humann（不支持直接 -1/-2）
- 数据库路径任一缺失时停止并列出缺失项
- 不编造数据库版本号

## Errors and Fallback

| 错误 | 处理 |
|---|---|
| ChocoPhlAn 找不到 | 检查 humann_nucleotide_db 路径下是否有 .ffn.gz 文件 |
| UniRef90 .dmnd 不存在 | 检查 humann_protein_db 路径下是否有 .dmnd 文件 |
| metaphlan 内部报错数据库版本不匹配 | 确认 bowtie2db 与 HUMAnN 版本对应 |

## Citation

- HUMAnN3: Franzosa et al., Nat Methods 2018. https://github.com/biobakery/humann
- bioBakery: McIver et al., Bioinformatics 2018
