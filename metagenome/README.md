# Metagenome Pipeline Skills

这是一个将宏基因组分析流程拆分为独立步骤 skill 的技能包。当前已经按 1 step = 1 skill 的方式整理为 10 个分析步骤，并统一了技能文档结构、软件管理策略、安装脚本与运行脚本组织方式。

## 总体目标

本技能包面向一条典型的 assembly-based metagenome analysis workflow，覆盖：

1. Raw read quality control
2. Taxonomic classification
3. Metagenomic assembly
4. CDS prediction
5. Non-redundant gene-set construction
6. Functional annotation
7. Representative protein structure-set construction
8. Metagenomic binning
9. Non-redundant genome-set construction and MAG annotation
10. BGC mining and comparative analysis

## Skills 列表

| Skill | Step | 主要软件 | 用途 |
|-------|------|----------|------|
| `quality-control` | 1 | fastp v0.20.1 | raw reads 质控，输出 clean reads 与 fastp 报告 |
| `taxonomic-classification` | 2 | MetaPhlAn4 v4.1.0 | clean reads 物种分类与分层级丰度表 |
| `metagenomic-assembly` | 3 | MEGAHIT v1.2.9 | clean reads 组装生成 contigs |
| `gene-prediction` | 4 | MetaGeneMark v3.38 | contigs 上 CDS 预测、翻译与完整性分类 |
| `nonredundant-gene-sets` | 5 | MMseqs2 v14-7e28 | biome 级非冗余基因集与蛋白家族聚类 |
| `functional-annotation` | 6 | eggNOG-mapper v2.1.9 / DIAMOND v2.1.6 / RGI v6.0.3 | NR gene set 功能注释、CAZy 注释、CARD 注释 |
| `protein-structure-prediction` | 7 | BLASTP v2.16.0 / ESMFold | 代表蛋白结构集构建与置信度分级 |
| `metagenomic-binning` | 8 | MetaWRAP v1.3 / CheckM v1.2.2 | MAG 恢复与质量过滤 |
| `nonredundant-genome-sets` | 9 | dRep v3.3.0 / GTDB-Tk v2.3.2 / Prodigal v2.6.3 / DIAMOND v2.1.6 | MAG 去冗余、分类与 ORF/功能注释 |
| `bgc-analysis` | 10 | antiSMASH v7.1.0 / BiG-SCAPE v2.0.0b8 | BGC 识别、聚类与专题比较分析 |

## 工作流关系

推荐的顺序关系如下：

- Step 1 → Step 2 → Step 3
- Step 3 → Step 4 → Step 5 → Step 6 → Step 7
- Step 3 + Step 1 → Step 8 → Step 9 → Step 10

说明：

- Step 2 是 read-based taxonomic profiling 分支，与 assembly-based 主线并行。
- Step 7 依赖 Step 4 和 Step 5 的结果，尤其是 complete CDS 蛋白与蛋白家族聚类结果。
- Step 10 依赖 Step 9 中整理好的 MAG / 基因组集合。

## 目录约定

每个 skill 使用如下结构：

- `<skill-name>/SKILL.md`
- `<skill-name>/scripts/...`
- 公共辅助脚本放在 `skills/_shared/`

当前目录树核心结构如下：

- skills/_shared/conda_env_helpers.sh
- skills/quality-control/
- skills/taxonomic-classification/
- skills/metagenomic-assembly/
- skills/gene-prediction/
- skills/nonredundant-gene-sets/
- skills/functional-annotation/
- skills/protein-structure-prediction/
- skills/metagenomic-binning/
- skills/nonredundant-genome-sets/
- skills/bgc-analysis/

## 统一文档规范

每个 SKILL.md 统一采用以下章节：

- YAML metadata 头
- Use When
- Do Not Use When（部分步骤可简化）
- Domain recognition
- Software environment
- Required inputs
- Necessary questions 或 Workflow
- Commands
- Output contract
- Guardrails
- Errors and fallback
- Examples

## 软件管理规范

当前版本统一采用以下原则：

1. 能稳定通过 conda 管理的软件，优先给出独立 conda 环境。
2. 每个步骤尽量提供：
   - 安装脚本
   - 运行脚本
3. 运行脚本不采用模糊 conda 判断，而是要求：
   - 显式传入 `--conda-env-name`，或
   - 显式传入 `--conda-env-prefix`
4. 激活环境后再次验证目标命令，避免激活失败却继续运行。
5. 对不适合直接 conda 管理的软件，改为显式软件路径或命令路径输入。
6. 推荐把 conda 环境安装到：
   `/home/{user_name}/software/conda-envs/`

## 公共辅助脚本

### `skills/_shared/conda_env_helpers.sh`

提供统一的 conda 环境辅助函数：

- `require_conda`
- `activate_conda_env`
- `ensure_command_after_activation`
- `print_active_conda_env`

作用：

- 统一 conda 激活逻辑
- 避免“检测到 conda 就尝试激活”的模糊行为
- 在每个 step 的运行脚本里做真实命令可用性校验

## 各步骤脚本清单

### Step 1: quality-control

- SKILL.md
- scripts/install_fastp_env.sh
- scripts/run_fastp_qc.sh

环境策略：独立 conda 环境，显式激活 fastp v0.20.1。

### Step 2: taxonomic-classification

- SKILL.md
- scripts/install_metaphlan4_env.sh
- scripts/run_metaphlan4_taxonomy.sh

环境策略：独立 conda 环境，显式激活 MetaPhlAn4 v4.1.0，并校验 `merge_metaphlan_tables.py`。

### Step 3: metagenomic-assembly

- SKILL.md
- scripts/install_megahit_env.sh
- scripts/run_megahit_assembly.sh

环境策略：独立 conda 环境，显式激活 MEGAHIT v1.2.9。

### Step 4: gene-prediction

- SKILL.md
- scripts/install_metagenemark_software.sh
- scripts/classify_metagenemark_cds.py
- scripts/run_metagenemark_prediction.sh

环境策略：MetaGeneMark 不默认假定可由 conda 稳定提供，改为显式传入：

- `--metagenemark-bin`
- `--model-file`

说明：这一步还包含 complete / 5'-truncated / 3'-truncated / both-truncated 的边界分类框架。

### Step 5: nonredundant-gene-sets

- SKILL.md
- scripts/install_mmseqs2_env.sh
- scripts/run_mmseqs2_gene_sets.sh

环境策略：独立 conda 环境，显式激活 MMseqs2。

### Step 6: functional-annotation

- SKILL.md
- scripts/install_annotation_env.sh
- scripts/run_functional_annotation.sh

环境策略：独立 conda 环境，集中管理：

- eggNOG-mapper
- DIAMOND
- RGI

数据库依赖需显式提供：

- eggNOG v5.0 database dir
- CAZy DIAMOND db
- CARD / RGI 相关数据库环境

### Step 7: protein-structure-prediction

- SKILL.md
- scripts/install_structure_env.sh
- scripts/run_structure_prediction.sh

环境策略：

- BLASTP 用 conda 环境管理
- ESMFold 采用显式命令路径 `--esmfold-cmd`

说明：当前已完成结构集构建框架、候选 cluster 过滤与命令组织；ESMFold 实际输出解析与代表结构精细筛选仍可继续增强。

### Step 8: metagenomic-binning

- SKILL.md
- scripts/install_binning_env.sh
- scripts/run_metawrap_binning.sh

环境策略：

- CheckM 等可用 conda 管理
- MetaWRAP 采用显式命令路径 `--metawrap-cmd`

说明：当前重点是把环境管理与命令组织写清楚；若项目中已有成熟 MetaWRAP 安装，可直接接入。

### Step 9: nonredundant-genome-sets

- SKILL.md
- scripts/install_mag_env.sh
- scripts/run_nr_genome_sets.sh

环境策略：独立 conda 环境，集中管理：

- dRep
- GTDB-Tk
- Prodigal
- DIAMOND

数据库依赖需显式提供：

- GTDB-Tk database
- COG database
- KEGG database

### Step 10: bgc-analysis

- SKILL.md
- scripts/install_bgc_env.sh
- scripts/run_bgc_analysis.sh

环境策略：

- antiSMASH 用 conda 环境管理
- BiG-SCAPE 通过显式命令路径 `--bigscape-cmd` 接入
- PFAM 目录通过 `--pfam-dir` 提供

说明：当前脚本已经整理了 antiSMASH 与 BiG-SCAPE 的运行框架，以及 microviridin 专题分析的人工复核提示。

