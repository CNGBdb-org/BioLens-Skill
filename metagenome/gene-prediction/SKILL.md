---
name: metagenome-gene-prediction
description: >-
  Metagenomic pipeline Step 4 coding-sequence prediction from assembled contigs using
  MetaGeneMark v3.38 with default parameters. Produces CDS/protein outputs and CDS
  completeness labels based on truncation symbols and strand-aware boundary status.
  Use after MEGAHIT assembly. Not for read-level QC or functional annotation.
compatibility: Bash, Python 3, MetaGeneMark v3.38
---

# Metagenome Gene Prediction

宏基因组流程 Step 4：使用 MetaGeneMark v3.38 从每个样本 contigs 预测 CDS，并结合截断符号与链方向判断 CDS 完整性。输出核酸序列、蛋白序列、完整 CDS 蛋白序列及完整性分类表。


## 文件与目录规范
所有生成的脚本和分析产物**不得放在 skills 目录下**。每次使用本 Skill 时，先在项目根目录（skills 同级）创建 outdir 结构：
```bash
PROJ_ROOT=$(dirname "$(dirname "$SKILLS_DIR")")   # skills 所在目录的上级
SKILL_OUTDIR="$PROJ_ROOT/outdir/metagenome-gene-prediction"
mkdir -p "$SKILL_OUTDIR/script"    # 生成的运行脚本
mkdir -p "$SKILL_OUTDIR/prosess"   # 分析中间文件
mkdir -p "$SKILL_OUTDIR/result"    # 最终结果文件
```
- script/   — 本次生成的运行脚本（如 gene-prediction_run_<date>.sh）
- prosess/  — 分析中间文件、临时目录
- result/   — 最终结果文件
## Use When

- 已完成宏基因组组装，已有 `temp/{sample}/assembly/{sample}.contigs.fa`
- 需要为后续非冗余基因集构建提供蛋白序列
- 需要区分 complete / 5'-truncated / 3'-truncated / both-truncated CDS

## Do Not Use When

| 需求 | 说明 |
|------|------|
| 原始 reads 质控 | 交给 `metagenome-quality-control` |
| 物种分类 | 交给 `metagenome-taxonomic-classification` |
| 功能注释 | 交给 `metagenome-functional-annotation` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 输入数据 | 每样本 contigs FASTA |
| 软件版本 | MetaGeneMark v3.38 |
| 软件管理 | 本地安装软件目录，不建议 conda |
| 密码子表 | codon table 11 |
| 单样本输出目录 | `temp/{sample}/metagenemark/` |

## Software environment

MetaGeneMark 通常涉及许可与模型文件，不建议假定可直接 conda 安装。本 Skill 采用“本地软件目录 + 显式路径参数”模式：

- 推荐安装目录：`/home/{user_name}/software/metagenemark-3.38`
- 安装脚本：`./scripts/install_metagenemark_software.sh`
- 运行脚本：`./scripts/run_metagenemark_prediction.sh`
- 必需文件：`gmhmmp` 可执行文件、模型文件 `MetaGeneMark_v1.mod`

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--sample-list` | 是 | 样本名列表文件 |
| `--temp-root` | 是 | 临时目录根，如 `temp/` |
| `--metagenemark-bin` | 是 | `gmhmmp` 可执行文件绝对路径 |
| `--model-file` | 是 | MetaGeneMark 模型文件路径 |
| `--codon-table` | 否 | 默认 11 |

## Necessary questions

1. 是否已获得 MetaGeneMark v3.38 本地安装包或可执行文件？
2. 模型文件 `MetaGeneMark_v1.mod` 路径是否明确？
3. 是否需要保留完整 CDS 蛋白序列作为后续 MMseqs2/BLASTP/ESMFold 输入？默认保留。

## Workflow

1. Gather：确认 contigs 路径、软件路径、模型文件路径
2. Install：必要时运行 `./scripts/install_metagenemark_software.sh`
3. Act：运行 `./scripts/run_metagenemark_prediction.sh`
4. Verify：检查每样本 `.gmm`、蛋白 FASTA、完整 CDS 表是否生成

## Commands

```bash
bash ./scripts/install_metagenemark_software.sh \
  --archive /path/to/MetaGeneMark_v3.38.tar.gz \
  --install-dir /home/{user_name}/software/metagenemark-3.38

bash ./scripts/run_metagenemark_prediction.sh \
  --sample-list /path/to/sample.txt \
  --temp-root /path/to/temp \
  --metagenemark-bin /home/{user_name}/software/metagenemark-3.38/gmhmmp \
  --model-file /home/{user_name}/software/metagenemark-3.38/MetaGeneMark_v1.mod \
  --codon-table 11
```

## Output contract

- `temp/{sample}/metagenemark/{sample}.gmm` — MetaGeneMark 主输出
- `temp/{sample}/metagenemark/{sample}_prot.fa` — 全部预测蛋白序列
- `temp/{sample}/metagenemark/{sample}_cds_status.tsv` — CDS 完整性分类表
- `temp/{sample}/metagenemark/{sample}_complete_prot.fa` — 完整 CDS 对应蛋白序列
- 不得虚构 CDS 数量或完整率统计结果

## Guardrails

- 软件版本固定参考 MetaGeneMark v3.38
- 使用默认参数，且翻译对应 codon table 11
- 运行时必须显式传入 `gmhmmp` 和模型文件路径
- 对完整性分类依赖 MetaGeneMark 输出中的截断边界标记；若输出格式不同需在结果中说明

## Errors and fallback

- 缺少 MetaGeneMark 软件或模型文件 → 先安装/提供本地路径
- contigs 缺失 → 报告缺失样本路径
- 输出格式与截断解析脚本不兼容 → 保留原始 `.gmm` 并回报需调整解析规则

## Examples

```bash
cd skills/metagenome-gene-prediction
bash ./scripts/run_metagenemark_prediction.sh \
  --sample-list /path/to/sample.txt \
  --temp-root /path/to/temp \
  --metagenemark-bin /home/{user_name}/software/metagenemark-3.38/gmhmmp \
  --model-file /home/{user_name}/software/metagenemark-3.38/MetaGeneMark_v1.mod
```
