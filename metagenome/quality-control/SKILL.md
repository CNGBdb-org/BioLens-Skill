---
name: metagenome-quality-control
description: >-
  Metagenomic pipeline Step 1 quality control using fastp v0.20.1 on paired-end raw
  FASTQ files. Produces cleaned reads plus JSON/HTML QC reports for downstream
  taxonomic profiling and assembly. Use when starting from raw metagenomic reads.
  Not for host decontamination, adapter redesign, or downstream taxonomic/assembly steps.
compatibility: Bash, conda, fastp v0.20.1
---

# Metagenome Quality Control

宏基因组流程 Step 1：使用 fastp v0.20.1 对双端 raw FASTQ 做质控，输出 clean reads、JSON 和 HTML 质控报告。优先调用包内脚本。

## Use When

- 输入是双端原始测序数据 `*_1.fastq.gz` 和 `*_2.fastq.gz`
- 需要为后续物种分类和组装生成 clean reads
- 需要保留 fastp 的 JSON 和 HTML 报告

## Do Not Use When

| 需求 | 说明 |
|------|------|
| 宿主去除 / 污染去除 | 不属于本 Skill 范围 |
| 物种分类 | 交给 `metagenome-taxonomic-classification` |
| 宏基因组组装 | 交给 `metagenome-metagenomic-assembly` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 输入数据 | paired-end FASTQ.gz |
| 软件版本 | fastp v0.20.1 |
| 软件管理 | conda 独立环境 |
| 参数策略 | 默认参数 |
| 单样本输出目录 | `temp/{sample}/fastp/` |

## 文件与目录规范
所有生成的脚本和分析产物**不得放在 skills 目录下**。每次使用本 Skill 时，先在项目根目录（skills 同级）创建 outdir 结构：
```bash
PROJ_ROOT=$(dirname "$(dirname "$SKILLS_DIR")")   # skills 所在目录的上级
SKILL_OUTDIR="$PROJ_ROOT/outdir/metagenome-quality-control"
mkdir -p "$SKILL_OUTDIR/script"    # 生成的运行脚本
mkdir -p "$SKILL_OUTDIR/prosess"   # 分析中间文件
mkdir -p "$SKILL_OUTDIR/result"    # 最终结果文件
```
- script/   — 本次生成的运行脚本（如 quality-control_run_<date>.sh）
- prosess/  — 分析中间文件、临时目录
- result/   — 最终结果文件

## Software environment
推荐将软件安装到独立 conda 环境，避免与其他步骤混用：
- 推荐环境名：`metagenome-fastp-0.20.1`
- 推荐环境前缀：`/home/{user_name}/software/conda-envs/metagenome-fastp-0.20.1`
- 安装脚本：`./scripts/install_fastp_env.sh`（skills 目录内只读参考）
- 运行脚本生成位置：`outdir/metagenome-quality-control/script/`
推荐安装方式：
```bash
bash /path/to/skills/metagenome-quality-control/scripts/install_fastp_env.sh \
  --env-prefix /home/{user_name}/software/conda-envs/metagenome-fastp-0.20.1
```

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--sample-list` | 是 | 样本名列表文件，每行一个 sample ID |
| `--seq-dir` | 是 | 原始 FASTQ 根目录，形如 `seq/{sample}/` |
| `--out-root` | 是 | 输出根目录，默认建议 `temp/` |
| `--threads` | 否 | fastp 线程数；若不传则用 fastp 默认 |
| `--conda-env-name` | 否 | conda 环境名，默认 `metagenome-fastp-0.20.1` |
| `--conda-env-prefix` | 否 | conda 环境绝对路径；传入后优先于环境名 |

## Necessary questions

1. 未给样本列表文件路径 → 补问 `sample.txt` 路径
2. FASTQ 命名不符合 `{sample}_1.fastq.gz` / `{sample}_2.fastq.gz` → 先确认命名规则
3. 若用户只提供 clean reads 而非 raw reads → 本 Skill 不适用
4. 若用户尚未安装 fastp v0.20.1 → 先运行安装脚本创建 conda 环境

## Workflow

1. Gather：确认样本列表、原始测序目录、输出目录、conda 环境位置
2. Install：必要时运行 `./scripts/install_fastp_env.sh`
3. Act：运行 `./scripts/run_fastp_qc.sh`
4. Verify：检查每个样本是否生成 clean reads、JSON、HTML

## Commands

```bash
bash ./scripts/install_fastp_env.sh \
  --env-prefix /home/{user_name}/software/conda-envs/metagenome-fastp-0.20.1

bash ./scripts/run_fastp_qc.sh \
  --sample-list /path/to/sample.txt \
  --seq-dir /path/to/seq \
  --out-root /path/to/temp \
  --conda-env-prefix /home/{user_name}/software/conda-envs/metagenome-fastp-0.20.1
```

## Output contract

- `temp/{sample}/fastp/{sample}_clean_1.fq.gz` — clean read 1
- `temp/{sample}/fastp/{sample}_clean_2.fq.gz` — clean read 2
- `temp/{sample}/fastp/{sample}_fastp.json` — fastp JSON 报告
- `temp/{sample}/fastp/{sample}_fastp.html` — fastp HTML 报告
- 不得虚构过滤率、Q30、reads 数等统计结果

## Guardrails

- 软件版本固定参考 fastp v0.20.1
- 参数按用户给定流程保持默认参数，不擅自加额外过滤阈值
- 目录命名保持与下游步骤兼容：`temp/{sample}/fastp/`
- 不使用“若检测到 conda 就尝试激活”的模糊逻辑；必须显式指定环境名或环境路径
- 激活环境后必须再次检查 `fastp` 是否真实可用

## Errors and fallback

- 缺少 conda → 先安装或配置 conda
- 缺少 fastp 环境 → 先运行安装脚本
- 输入 FASTQ 不存在 → 回报缺失文件路径
- 输出目录已存在旧结果 → 说明是否覆盖或复用

## Examples

**用户**：先把这批宏基因组双端 raw reads 做 fastp 质控，并明确使用独立 conda 环境

```bash
cd skills/metagenome-quality-control
bash ./scripts/install_fastp_env.sh \
  --env-prefix /home/{user_name}/software/conda-envs/metagenome-fastp-0.20.1
bash ./scripts/run_fastp_qc.sh \
  --sample-list /path/to/sample.txt \
  --seq-dir /path/to/seq \
  --out-root /path/to/temp \
  --conda-env-prefix /home/{user_name}/software/conda-envs/metagenome-fastp-0.20.1
```

**产出**：`temp/{sample}/fastp/` 下的 clean reads 与 fastp 报告
