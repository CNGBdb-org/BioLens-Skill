---
name: ckb-meta
description: >-
  CKB metagenomics analysis orchestrator for human gut microbiome shotgun sequencing.
  Covers the full pipeline: QC + host removal → assembly → binning → taxonomy profiling
  (MetaPhlAn4) → MAG quality (CheckM2) → taxonomy classification (GTDB-Tk) →
  functional annotation (HUMAnN3) → strain-level analysis (StrainPhlAn4) →
  pangenome (Prokka + Panaroo) → multi-sample merge → downstream statistics
  (community diversity, differential abundance, association network, machine learning,
  survival analysis, functional enrichment).
  Use when given metagenomics FASTQ, per-sample profiles, or merged abundance matrices
  from gut microbiome studies. Supports DCS WDL platform and any conda/Docker environment.
  Not for 16S amplicon (use amplicon skills), host genome analysis (use genomics skills),
  or single-cell (use sc-ingest / scanpy).
compatibility: "Python 3.10+; conda (biobakery3 / humann env) or DCS WDL platform; Linux x86_64"
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

# CKB-Meta 宏基因组分析编排 Skill

完整宏基因组流程编排器，覆盖从原始 FASTQ 到下游统计的全链路。

## 层级模型（硬边界）

| 层 | 输入 | 执行方式 | 产物 |
|---|---|---|---|
| upstream | 单样本 FASTQ / MAG | 工具逐样本运行 | per-sample profile / bins |
| merge | N 个样本 per-sample 产物 | 脚本合并 | 多样本矩阵 |
| downstream | merged 矩阵 + metadata | Python 脚本 | 统计结果 / 图 / 报告 |

## 路由规则（第一步必须判断）

1. 提供 FASTQ → 进 **upstream**，从 `ckb-meta-qc` 开始
2. 有 per-sample 结果未合并 → 进 **ckb-meta-merge**
3. 有 merged 矩阵 + metadata → 进 **downstream** 对应模块
4. 要求完整分析 → upstream → merge → downstream 串联
5. 提供中间产物（MAG/contigs/profile） → 判断 upstream 阶段，从对应 skill 继续

## Use When

- 拿到宏基因组 FASTQ（双端或单端），需要全流程分析
- 已有 per-sample MetaPhlAn4 profile，需要合并后做多组统计
- 已有 merged 物种丰度矩阵 + metadata，需要差异/多样性/ML 分析
- 需要功能注释（HUMAnN3）→ 功能差异分析
- 需要 MAG 重建 → 质控 → 物种分类全链路

## Do Not Use When

| 需求 | 交给 |
|---|---|
| 16S 扩增子 | 16S amplicon skills |
| 宿主基因组分析 | genomics skills |
| 单细胞转录组 | sc-ingest / scanpy |
| 单纯功能富集（非宏基因组来源） | go / kegg |

## 执行环境检测规则（所有 upstream skill 通用）

每个 upstream skill 在运行前，Agent 必须检查：

```
1. 检查 DCS 平台：命令 `dcs --version` 可用 → 使用 DCS WDL 投递
2. 检查 conda 环境：`conda env list` 中存在所需环境 → 激活后直接运行
3. 检查工具路径：`which <tool>` 可找到 → 直接调用
4. 以上均不满足 → 告知用户缺失哪些软件/数据库，提供安装指引，停止执行
```

**不编造工具路径，不跳过检测步骤。**

## 子 Skill 索引

### Upstream（9 个，逐样本）

| Skill | 功能 | DCS WDL |
|---|---|---|
| `ckb-meta-qc` | fastp 质控 + Bowtie2 去宿主 | `qc_skill` |
| `ckb-meta-assembly` | MEGAHIT 组装 | `Megahit_skill` |
| `ckb-meta-binning` | Bowtie2 回贴 + SemiBin2 分箱 | `bowtie_Semibin2_skill` |
| `ckb-meta-taxonomy` | MetaPhlAn4 物种 profile | `metaphlan4_skill` |
| `ckb-meta-checkm2` | CheckM2 MAG 质控 | `CheckM_skill` |
| `ckb-meta-gtdbtk` | GTDB-Tk r226 物种分类 | `gtdbtk_skill_noway` |
| `ckb-meta-humann` | HUMAnN3 功能注释（PE/SE） | `rmhost_humann_PE` / `rmhost_humann_SE` |
| `ckb-meta-strainphlan` | StrainPhlAn4 菌株建树 | `strainphlan4_skill` |
| `ckb-meta-pangenome` | Prokka 注释 + Panaroo 泛基因组 | `prokka_panaroo_skill` |

### Merge（1 个）

| Skill | 功能 |
|---|---|
| `ckb-meta-merge` | MetaPhlAn4 合并 / HUMAnN3 合并 / MAG 去冗余 |

### Downstream（6 个，多样本）

| Skill | 功能 | 必要输入 |
|---|---|---|
| `ckb-meta-community` | alpha/beta 多样性、PCoA、PERMANOVA | abundance matrix + group col |
| `ckb-meta-differential` | 差异丰度分析 | abundance matrix + group col |
| `ckb-meta-association` | 表型关联 / 共丰度网络 | abundance matrix + phenotype cols |
| `ckb-meta-machine-learning` | 分类建模、ROC/PR、biomarker | abundance matrix + label col |
| `ckb-meta-survival` | Cox 回归、KM 曲线、timeROC | abundance matrix + time col + status col |
| `ckb-meta-functional` | 功能差异、通路富集 | function matrix + group col |

## 缺失信息处理

| 缺少 | 行为 |
|---|---|
| group / label col | 停止，要求用户提供分组信息 |
| time / status col（生存分析）| 停止，要求提供 |
| merged 矩阵（只有 per-sample）| 引导进 ckb-meta-merge |
| metadata 文件 | 停止，要求提供 |
| 软件/数据库未安装 | 列出缺失项 + 版本 + 下载地址，不执行分析 |

## Citation

- MetaPhlAn4: Blanco-Míguez et al., Nat Methods 2023
- HUMAnN3: Franzosa et al., Nat Methods 2018
- MEGAHIT: Li et al., Bioinformatics 2015
- SemiBin2: Pan et al., Nat Commun 2023
- CheckM2: Chklovski et al., Nat Methods 2023
- GTDB-Tk r226: Parks et al., Nat Biotechnol 2022
- StrainPhlAn4: Costea et al., Nat Methods 2017
- Panaroo: Tonkin-Hill et al., Genome Biol 2020
