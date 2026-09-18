---
name: metagenome-metagenomic-assembly
description: >-
  Metagenomic pipeline Step 3 de novo assembly using MEGAHIT v1.2.9 with
  `--presets meta-sensitive` on fastp-cleaned paired-end FASTQ files. Produces
  per-sample assembly directories and contig FASTA files for downstream gene
  prediction and binning. Use after quality control. Not for taxonomic profiling.
compatibility: Bash, conda, MEGAHIT v1.2.9
---

# Metagenome Metagenomic Assembly

宏基因组流程 Step 3：使用 MEGAHIT v1.2.9 对 fastp clean reads 进行 de novo 组装，核心参数为 `--presets meta-sensitive`。输出每个样本的 assembly 目录和 contigs 文件。优先调用包内脚本。


## 文件与目录规范
所有生成的脚本和分析产物**不得放在 skills 目录下**。每次使用本 Skill 时，先在项目根目录（skills 同级）创建 outdir 结构：
```bash
PROJ_ROOT=$(dirname "$(dirname "$SKILLS_DIR")")   # skills 所在目录的上级
SKILL_OUTDIR="$PROJ_ROOT/outdir/metagenome-metagenomic-assembly"
mkdir -p "$SKILL_OUTDIR/script"    # 生成的运行脚本
mkdir -p "$SKILL_OUTDIR/prosess"   # 分析中间文件
mkdir -p "$SKILL_OUTDIR/result"    # 最终结果文件
```
- script/   — 本次生成的运行脚本（如 metagenomic-assembly_run_<date>.sh）
- prosess/  — 分析中间文件、临时目录
- result/   — 最终结果文件
## Use When

- 已完成 fastp 质控，并已有 clean paired-end FASTQ
- 需要生成 contigs 用于基因预测、binning、后续功能分析
- 希望保持与既有流程一致的 `meta-sensitive` 组装参数

## Do Not Use When

| 需求 | 说明 |
|------|------|
| 原始 reads 质控 | 交给 `metagenome-quality-control` |
| 物种分类 | 交给 `metagenome-taxonomic-classification` |
| 基因预测 / binning | 不属于本 Skill 范围 |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 输入数据 | fastp clean paired FASTQ.gz |
| 软件版本 | MEGAHIT v1.2.9 |
| 软件管理 | conda 独立环境 |
| 核心参数 | `--presets meta-sensitive` |
| 单样本输出目录 | `temp/{sample}/assembly/` |

## Software environment

推荐将软件安装到独立 conda 环境，避免与其他步骤混用：

- 推荐环境名：`metagenome-megahit-1.2.9`
- 推荐环境前缀：`/home/{user_name}/software/conda-envs/metagenome-megahit-1.2.9`
- 安装脚本：`./scripts/install_megahit_env.sh`
- 运行脚本：`./scripts/run_megahit_assembly.sh`

推荐安装方式：

```bash
bash ./scripts/install_megahit_env.sh \
  --env-prefix /home/{user_name}/software/conda-envs/metagenome-megahit-1.2.9
```

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--sample-list` | 是 | 样本名列表文件 |
| `--temp-root` | 是 | 共享临时目录根，如 `temp/` |
| `--threads` | 否 | MEGAHIT 线程数，默认 10 |
| `--conda-env-name` | 否 | conda 环境名，默认 `metagenome-megahit-1.2.9` |
| `--conda-env-prefix` | 否 | conda 环境绝对路径；传入后优先于环境名 |

## Necessary questions

1. 未完成 fastp 质控 → 先运行 `metagenome-quality-control`
2. clean reads 路径不符合 `temp/{sample}/fastp/{sample}_clean_1.fq.gz` 规则 → 先确认路径规范
3. 若用户想使用不同 preset 或组装器 → 需要明确是否偏离当前标准流程
4. 若用户尚未安装 MEGAHIT v1.2.9 → 先运行安装脚本创建 conda 环境

## Workflow

1. Gather：确认样本列表、temp 根目录、conda 环境位置、线程数
2. Install：必要时运行 `./scripts/install_megahit_env.sh`
3. Act：运行 `./scripts/run_megahit_assembly.sh`
4. Verify：检查每样本 assembly 目录和 contigs 文件是否生成

## Commands

```bash
bash ./scripts/install_megahit_env.sh \
  --env-prefix /home/{user_name}/software/conda-envs/metagenome-megahit-1.2.9

bash ./scripts/run_megahit_assembly.sh \
  --sample-list /path/to/sample.txt \
  --temp-root /path/to/temp \
  --threads 10 \
  --conda-env-prefix /home/{user_name}/software/conda-envs/metagenome-megahit-1.2.9
```

## Output contract

- `temp/{sample}/assembly/` — 单样本组装目录
- `temp/{sample}/assembly/{sample}.contigs.fa` — 主 contigs FASTA
- `temp/{sample}/assembly/intermediate_contigs/` — 组装中间结果（若 MEGAHIT 生成）
- `temp/{sample}/assembly/log` — 运行日志（若 MEGAHIT 生成）
- 不得虚构 N50、contig 数、总组装长度等统计值

## Guardrails

- 软件版本固定参考 MEGAHIT v1.2.9
- 参数保持 `--presets meta-sensitive`
- 输出目录命名保持与下游基因预测步骤兼容：`temp/{sample}/assembly/`
- 不使用“检测到 conda 就尝试 activate”的模糊逻辑；必须显式指定环境名或环境路径
- 激活环境后必须再次检查 `megahit` 是否真实可用

## Errors and fallback

- 缺少 conda → 先安装或配置 conda
- 缺少 MEGAHIT 环境 → 先创建环境
- clean reads 缺失 → 报告缺失样本路径
- 磁盘空间不足或内存不足 → 提示减少并发或切换更大资源

## Examples

**用户**：用 clean reads 做宏基因组组装，并明确使用独立 conda 环境

```bash
cd skills/metagenome-metagenomic-assembly
bash ./scripts/install_megahit_env.sh \
  --env-prefix /home/{user_name}/software/conda-envs/metagenome-megahit-1.2.9
bash ./scripts/run_megahit_assembly.sh \
  --sample-list /path/to/sample.txt \
  --temp-root /path/to/temp \
  --threads 10 \
  --conda-env-prefix /home/{user_name}/software/conda-envs/metagenome-megahit-1.2.9
```

**产出**：`temp/{sample}/assembly/{sample}.contigs.fa`
