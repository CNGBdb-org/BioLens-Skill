---
name: metagenome-functional-annotation
description: >-
  Metagenomic pipeline Step 6 functional annotation of non-redundant gene sets using
  eggNOG-mapper v2.1.9 against eggNOG v5.0, DIAMOND v2.1.6 against CAZy, and RGI
  v6.0.3 against CARD.
compatibility: Bash, conda, eggNOG-mapper v2.1.9, DIAMOND v2.1.6, RGI v6.0.3
---

# Metagenome Functional Annotation

宏基因组流程 Step 6：使用 eggNOG-mapper 做广义功能注释，使用 DIAMOND 做 CAZy 专项注释，使用 RGI 做 CARD 抗性基因识别。


## 文件与目录规范
所有生成的脚本和分析产物**不得放在 skills 目录下**。每次使用本 Skill 时，先在项目根目录（skills 同级）创建 outdir 结构：
```bash
PROJ_ROOT=$(dirname "$(dirname "$SKILLS_DIR")")   # skills 所在目录的上级
SKILL_OUTDIR="$PROJ_ROOT/outdir/metagenome-functional-annotation"
mkdir -p "$SKILL_OUTDIR/script"    # 生成的运行脚本
mkdir -p "$SKILL_OUTDIR/prosess"   # 分析中间文件
mkdir -p "$SKILL_OUTDIR/result"    # 最终结果文件
```
- script/   — 本次生成的运行脚本（如 functional-annotation_run_<date>.sh）
- prosess/  — 分析中间文件、临时目录
- result/   — 最终结果文件
## Use When

- 已完成 biome 级非冗余基因集构建
- 需要对非冗余蛋白做综合功能注释与专项数据库注释
- 已准备好 eggNOG/CAZy/CARD 对应数据库

## Do Not Use When

| 需求 | 说明 |
|------|------|
| 非冗余蛋白聚类 | 交给 `metagenome-nonredundant-gene-sets` |
| 蛋白结构预测 | 交给 `metagenome-protein-structure-prediction` |
| MAG 注释 | 交给 `metagenome-nonredundant-genome-sets` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 输入数据 | biome 级非冗余蛋白序列 |
| 软件版本 | eggNOG-mapper 2.1.9 / DIAMOND 2.1.6 / RGI 6.0.3 |
| 软件管理 | conda 独立环境 |
| 数据库依赖 | eggNOG v5.0 / CAZy / CARD |

## Software environment

- 推荐环境名：`metagenome-annotation-stack`
- 推荐环境前缀：`/home/{user_name}/software/conda-envs/metagenome-annotation-stack`
- 安装脚本：`./scripts/install_annotation_env.sh`
- 运行脚本：`./scripts/run_functional_annotation.sh`

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--geneset-root` | 是 | `result/geneset/` 根目录 |
| `--eggnog-db-dir` | 是 | eggNOG v5.0 数据库目录 |
| `--cazy-db` | 是 | CAZy DIAMOND 数据库 |
| `--threads` | 否 | 线程数，默认 20 |
| `--conda-env-name / --conda-env-prefix` | 否 | conda 环境名或绝对路径 |

## Workflow

1. Gather：确认非冗余 FASTA 和数据库路径
2. Install：必要时运行 `./scripts/install_annotation_env.sh`
3. Act：运行 `./scripts/run_functional_annotation.sh`
4. Verify：检查 eggNOG、CAZy、CARD 结果文件是否生成

## Output contract

- `result/geneset/{biome}/eggnog/{biome}.emapper.annotations`
- `result/geneset/{biome}/cazy/{biome}_cazy.tsv`
- `result/geneset/{biome}/card/{biome}_card.txt`

## Guardrails

- eggNOG-mapper 使用默认参数，对应 eggNOG v5.0 数据库
- DIAMOND CAZy 注释固定参数 `blastp -e 0.00001 --more-sensitive --outfmt 6`
- RGI 固定参数 `--local --clean --include_loose -t protein`
- CARD/eggNOG/CAZy 数据库路径必须由用户或项目显式提供

## Examples

```bash
cd skills/metagenome-functional-annotation
bash ./scripts/install_annotation_env.sh \
  --env-prefix /home/{user_name}/software/conda-envs/metagenome-annotation-stack
bash ./scripts/run_functional_annotation.sh \
  --geneset-root /path/to/result/geneset \
  --eggnog-db-dir /path/to/eggnog_v5 \
  --cazy-db /path/to/cazy.dmnd \
  --threads 20 \
  --conda-env-prefix /home/{user_name}/software/conda-envs/metagenome-annotation-stack
```
