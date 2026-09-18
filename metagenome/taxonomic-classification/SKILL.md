---
name: metagenome-taxonomic-classification
description: >-
  Metagenomic pipeline Step 2 taxonomic classification using MetaPhlAn4 v4.1.0 on
  fastp-cleaned paired-end FASTQ files. Produces per-sample taxonomic profiles,
  bowtie2 intermediate output, merged abundance table, and rank-specific abundance
  tables. Use after quality control. Not for functional annotation or assembly.
compatibility: Bash, conda, MetaPhlAn4 v4.1.0
---

# Metagenome Taxonomic Classification

宏基因组流程 Step 2：使用 MetaPhlAn4 v4.1.0 对 fastp clean reads 做物种分类，输出每样本分类结果、bowtie2 中间文件、合并丰度表以及不同分类层级的丰度矩阵。优先调用包内脚本。


## 文件与目录规范
所有生成的脚本和分析产物**不得放在 skills 目录下**。每次使用本 Skill 时，先在项目根目录（skills 同级）创建 outdir 结构：
```bash
PROJ_ROOT=$(dirname "$(dirname "$SKILLS_DIR")")   # skills 所在目录的上级
SKILL_OUTDIR="$PROJ_ROOT/outdir/metagenome-taxonomic-classification"
mkdir -p "$SKILL_OUTDIR/script"    # 生成的运行脚本
mkdir -p "$SKILL_OUTDIR/prosess"   # 分析中间文件
mkdir -p "$SKILL_OUTDIR/result"    # 最终结果文件
```
- script/   — 本次生成的运行脚本（如 taxonomic-classification_run_<date>.sh）
- prosess/  — 分析中间文件、临时目录
- result/   — 最终结果文件
## Use When

- 已完成 fastp 质控，并已有 clean paired-end FASTQ
- 需要获得 MetaPhlAn4 物种组成结果
- 需要进一步导出 species / genus / family / order / class / phylum 丰度表

## Do Not Use When

| 需求 | 说明 |
|------|------|
| 原始 reads 质控 | 交给 `metagenome-quality-control` |
| 宏基因组组装 | 交给 `metagenome-metagenomic-assembly` |
| 功能注释或基因预测 | 不属于本 Skill 范围 |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 输入数据 | fastp clean paired FASTQ.gz |
| 软件版本 | MetaPhlAn4 v4.1.0 |
| 软件管理 | conda 独立环境 |
| 核心参数 | `--input_type fastq -o sample.txt --bowtie2out sample.bz2` |
| 单样本输出目录 | `temp/{sample}/mp4/` |

## Software environment

推荐将软件安装到独立 conda 环境，避免与其他步骤混用：

- 推荐环境名：`metagenome-metaphlan4-4.1.0`
- 推荐环境前缀：`/home/{user_name}/software/conda-envs/metagenome-metaphlan4-4.1.0`
- 安装脚本：`./scripts/install_metaphlan4_env.sh`
- 运行脚本：`./scripts/run_metaphlan4_taxonomy.sh`

推荐安装方式：

```bash
bash ./scripts/install_metaphlan4_env.sh \
  --env-prefix /home/{user_name}/software/conda-envs/metagenome-metaphlan4-4.1.0
```

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--sample-list` | 是 | 样本名列表文件 |
| `--temp-root` | 是 | 上一步和本步骤共享的临时目录根，如 `temp/` |
| `--threads` | 否 | MetaPhlAn4 线程数，默认 10 |
| `--conda-env-name` | 否 | conda 环境名，默认 `metagenome-metaphlan4-4.1.0` |
| `--conda-env-prefix` | 否 | conda 环境绝对路径；传入后优先于环境名 |

## Necessary questions

1. 未完成 fastp 质控 → 先运行 `metagenome-quality-control`
2. clean reads 路径不符合 `temp/{sample}/fastp/{sample}_clean_1.fq.gz` 规则 → 先确认路径规范
3. 用户是否需要导出分层级丰度矩阵 → 默认生成全部层级表
4. 若用户尚未安装 MetaPhlAn4 v4.1.0 → 先运行安装脚本创建 conda 环境

## Workflow

1. Gather：确认样本列表、temp 根目录、conda 环境位置、线程数
2. Install：必要时运行 `./scripts/install_metaphlan4_env.sh`
3. Act：运行 `./scripts/run_metaphlan4_taxonomy.sh`
4. Verify：检查每样本 `.txt`、`.bz2`、merged abundance table 与 rank tables

## Commands

```bash
bash ./scripts/install_metaphlan4_env.sh \
  --env-prefix /home/{user_name}/software/conda-envs/metagenome-metaphlan4-4.1.0

bash ./scripts/run_metaphlan4_taxonomy.sh \
  --sample-list /path/to/sample.txt \
  --temp-root /path/to/temp \
  --threads 10 \
  --conda-env-prefix /home/{user_name}/software/conda-envs/metagenome-metaphlan4-4.1.0
```

## Output contract

- `temp/{sample}/mp4/{sample}.txt` — 单样本 MetaPhlAn4 分类结果
- `temp/{sample}/mp4/bowtie2out_{sample}.bz2` — bowtie2 中间输出
- `temp/metaphlan_merged/merged_abundance_table.txt` — 合并丰度表
- `temp/metaphlan_merged/merged_abundance_species.txt` — species 丰度表
- `temp/metaphlan_merged/merged_abundance_genus.txt` — genus 丰度表
- `temp/metaphlan_merged/merged_abundance_family.txt` — family 丰度表
- `temp/metaphlan_merged/merged_abundance_order.txt` — order 丰度表
- `temp/metaphlan_merged/merged_abundance_class.txt` — class 丰度表
- `temp/metaphlan_merged/merged_abundance_phylum.txt` — phylum 丰度表
- 不得虚构优势菌、alpha 多样性或统计检验结果

## Guardrails

- 软件版本固定参考 MetaPhlAn4 v4.1.0
- 保留 `--input_type fastq` 和 `--bowtie2out`
- 相比原始脚本，`merge_metaphlan_tables.py` 应对所有样本统一合并一次，避免在样本循环内重复覆盖文件
- 不使用“检测到 conda 就尝试 activate”的模糊逻辑；必须显式指定环境名或环境路径
- 激活环境后必须检查 `metaphlan` 与 `merge_metaphlan_tables.py` 都可真实调用

## Errors and fallback

- 缺少 conda → 先安装或配置 conda
- 缺少 MetaPhlAn4 环境或数据库 → 先创建环境，并检查数据库配置
- 某些样本 clean reads 缺失 → 报告缺失样本并停止合并
- `merge_metaphlan_tables.py` 不可用 → 检查 MetaPhlAn 安装路径

## Examples

**用户**：对 clean reads 做 MetaPhlAn4 物种分类，并明确使用独立 conda 环境

```bash
cd skills/metagenome-taxonomic-classification
bash ./scripts/install_metaphlan4_env.sh \
  --env-prefix /home/{user_name}/software/conda-envs/metagenome-metaphlan4-4.1.0
bash ./scripts/run_metaphlan4_taxonomy.sh \
  --sample-list /path/to/sample.txt \
  --temp-root /path/to/temp \
  --threads 10 \
  --conda-env-prefix /home/{user_name}/software/conda-envs/metagenome-metaphlan4-4.1.0
```

**产出**：`temp/{sample}/mp4/` 单样本结果，以及 `temp/metaphlan_merged/` 下的 merged abundance tables
