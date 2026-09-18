---
name: metagenome-bgc-analysis
description: >-
  Metagenomic pipeline Step 10 biosynthetic gene-cluster discovery and comparative
  analysis in MAGs using antiSMASH v7.1.0, BiG-SCAPE v2.0.0b8, GTDB-Tk, iTOL and
  Clinker-oriented downstream organization.
compatibility: Bash, conda, antiSMASH v7.1.0, BiG-SCAPE v2.0.0b8
---

# Metagenome BGC Analysis

宏基因组流程 Step 10：在 MAG 中识别 BGC，进行 BiG-SCAPE 聚类，并为 microviridin 等专题分析整理宿主、系统发育、结构比较与下游可视化输入文件。

## Use When

- 输入是按 biome 组织的 MAG 基因组序列（`{biome}/genomes/*.fa`）
- 需要识别 BGC（生物合成基因簇）并用 BiG-SCAPE 聚类比较
- 需要对 microviridin 等专题做手工核查准备

## Do Not Use When

| 需求 | 说明 |
|------|------|
| MAG 尚未恢复或质控 | 交给 `metagenome-metagenomic-binning` 或 `metagenome-nonredundant-genome-sets` |
| 只需物种分类，无需 BGC 挖掘 | 不属于本 Skill 范围 |
| iTOL / Clinker 可视化 | 下游展示步骤，本 Skill 不自动执行 |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 输入数据 | MAG 基因组 FASTA（.fa），按 biome 子目录组织 |
| antiSMASH 版本 | v7.1.0 |
| BiG-SCAPE 版本 | v2.0.0b8 |
| 软件管理 | conda 独立环境 |
| 参数策略 | 固定参数（见 Guardrails） |
| 单 biome 输出目录 | `{output_root}/{biome}/antismash/` + `bigscape_result/` |

## 文件与目录规范
所有生成的脚本和分析产物**不得放在 skills 目录下**。每次使用本 Skill 时，先在项目根目录（skills 同级）创建 outdir 结构：
```bash
PROJ_ROOT=$(dirname "$(dirname "$SKILLS_DIR")")   # skills 所在目录的上级
SKILL_OUTDIR="$PROJ_ROOT/outdir/metagenome-bgc-analysis"
mkdir -p "$SKILL_OUTDIR/script"    # 生成的运行脚本
mkdir -p "$SKILL_OUTDIR/prosess"   # 分析中间文件
mkdir -p "$SKILL_OUTDIR/result"    # 最终结果文件
```
- script/   — 本次生成的运行脚本（如 bgc-analysis_run_<date>.sh）
- prosess/  — 分析中间文件、临时目录
- result/   — 最终结果文件

## Software environment

- 推荐环境名：`metagenome-bgc-stack`
- 推荐环境前缀：`/home/{user_name}/software/conda-envs/metagenome-bgc-stack`
- 安装脚本：`./scripts/install_bgc_env.sh`
- 运行脚本：`./scripts/run_bgc_analysis.sh`

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--genomeset-root` | 是 | MAG 根目录，子目录按 biome 组织，每个 biome 下含 `genomes/*.fa` |
| `--output-root` | 是 | 输出根目录，建议 `result/bgcset` |
| `--pfam-dir` | 是 | Pfam HMM 数据库目录（BiG-SCAPE 必需）|
| `--bigscape-cmd` | 否 | BiG-SCAPE 命令，默认 `bigscape.py` |
| `--threads` | 否 | 线程数，默认 20 |
| `--conda-env-name` | 否 | conda 环境名，默认 `metagenome-bgc-stack` |
| `--conda-env-prefix` | 否 | conda 环境绝对路径；传入后优先于环境名 |

## Necessary questions

1. 未给 MAG 目录路径 → 补问 `--genomeset-root` 及其目录结构
2. 未给 Pfam 数据库路径 → 补问 `--pfam-dir`（BiG-SCAPE 必需）
3. BiG-SCAPE 未在 PATH 中 → 确认 `--bigscape-cmd` 参数
4. 尚未安装 antiSMASH / BiG-SCAPE 环境 → 先运行安装脚本

## Workflow

1. Gather：确认 MAG 目录结构、输出目录、Pfam 数据库路径、conda 环境位置
2. Install：必要时运行 `./scripts/install_bgc_env.sh`
3. Act：运行 `./scripts/run_bgc_analysis.sh`
4. Verify：检查每个 biome 是否生成 antiSMASH 结果、`all_gbk/` 目录及 BiG-SCAPE 输出

## Commands

```bash
bash ./scripts/install_bgc_env.sh \
  --env-prefix /home/{user_name}/software/conda-envs/metagenome-bgc-stack

bash ./scripts/run_bgc_analysis.sh \
  --genomeset-root /path/to/result/genomeset \
  --output-root /path/to/result/bgcset \
  --pfam-dir /path/to/pfam \
  --conda-env-prefix /home/{user_name}/software/conda-envs/metagenome-bgc-stack
```

## Output contract

- `{output_root}/{biome}/antismash/result/{genome}/` — antiSMASH 各基因组输出目录
- `{output_root}/{biome}/antismash/all_gbk/` — 收集的 region GBK 文件（BiG-SCAPE 输入）
- `{output_root}/{biome}/bigscape_result/` — BiG-SCAPE 聚类结果
- `{output_root}/{biome}/microviridin_review/README.txt` — microviridin 手工核查提示
- 不得虚构 BGC 数量、GCF 聚类数等统计结果

## Guardrails

- antiSMASH 固定参数：`--genefinding-tool prodigal --cb-knownclusters`
- BiG-SCAPE 固定参数：`--mix --hybrids-off --gcf-cutoffs 0.3,0.7 -m 4.0`
- microviridin 检索应保留 ATP-grasp ligase 与 TxKxPSD motif 的手工核查位点说明
- iTOL / Clinker 属于下游展示与比较，不应伪装成自动已完成结果

## Errors and fallback

- 缺少 conda → 先安装或配置 conda
- 缺少 antiSMASH 环境 → 先运行安装脚本
- BiG-SCAPE 命令不存在 → 确认 `--bigscape-cmd` 参数或手动安装
- MAG 目录下无 `.fa` 文件 → 检查 `--genomeset-root` 目录结构是否符合 `{biome}/genomes/*.fa`
- 输出目录已存在旧结果 → 说明是否覆盖或复用
