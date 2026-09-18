---
name: metagenome-nonredundant-gene-sets
description: >-
  Metagenomic pipeline Step 5 non-redundant gene-set construction using MMseqs2
  v14-7e28. First deduplicates proteins within the same biome using
  easy-cluster --min-seq-id 0.95 -c 0.90 --cov-mode 1 --cluster-mode 3, then
  performs protein-family clustering with --min-seq-id 0.20 -c 0.50.
compatibility: Bash, conda, MMseqs2 v14-7e28
---

# Metagenome Non-redundant Gene Sets

宏基因组流程 Step 5：先对同一 biome 多样本蛋白序列做 95% identity 去冗余，得到非冗余基因集；再对单个极端生境的非冗余序列做 20% identity 的蛋白家族聚类。


## 文件与目录规范
所有生成的脚本和分析产物**不得放在 skills 目录下**。每次使用本 Skill 时，先在项目根目录（skills 同级）创建 outdir 结构：
```bash
PROJ_ROOT=$(dirname "$(dirname "$SKILLS_DIR")")   # skills 所在目录的上级
SKILL_OUTDIR="$PROJ_ROOT/outdir/metagenome-nonredundant-gene-sets"
mkdir -p "$SKILL_OUTDIR/script"    # 生成的运行脚本
mkdir -p "$SKILL_OUTDIR/prosess"   # 分析中间文件
mkdir -p "$SKILL_OUTDIR/result"    # 最终结果文件
```
- script/   — 本次生成的运行脚本（如 nonredundant-gene-sets_run_<date>.sh）
- prosess/  — 分析中间文件、临时目录
- result/   — 最终结果文件
## Use When

- 已完成 MetaGeneMark 蛋白预测
- 样本已经按照 biome 分组
- 需要构建 biome 级非冗余蛋白集与蛋白家族聚类

## Do Not Use When

| 需求 | 说明 |
|------|------|
| 单样本 CDS 预测 | 交给 `metagenome-gene-prediction` |
| 功能注释 | 交给 `metagenome-functional-annotation` |
| 蛋白结构预测 | 交给 `metagenome-protein-structure-prediction` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 输入数据 | MetaGeneMark 蛋白序列 |
| 软件版本 | MMseqs2 v14-7e28 |
| 软件管理 | conda 独立环境 |
| biome 映射 | `biome_list/*.txt`，每个文件列一个 biome 下的样本 |

## Software environment

- 推荐环境名：`metagenome-mmseqs2-14-7e28`
- 推荐环境前缀：`/home/{user_name}/software/conda-envs/metagenome-mmseqs2-14-7e28`
- 安装脚本：`./scripts/install_mmseqs2_env.sh`
- 运行脚本：`./scripts/run_mmseqs2_gene_sets.sh`

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--biome-list-dir` | 是 | biome 列表目录 |
| `--temp-root` | 是 | 临时目录根，如 `temp/` |
| `--output-root` | 是 | 输出根目录，如 `result/geneset/` |
| `--threads` | 否 | 线程数，默认 20 |
| `--conda-env-name / --conda-env-prefix` | 否 | conda 环境名或绝对路径 |

## Workflow

1. Gather：确认样本分组文件、蛋白路径、输出路径
2. Install：必要时运行 `./scripts/install_mmseqs2_env.sh`
3. Act：运行 `./scripts/run_mmseqs2_gene_sets.sh`
4. Verify：检查聚合 FASTA、代表序列、cluster TSV 是否生成

## Output contract

- `result/geneset/{biome}/{biome}_all_prot.fa`
- `result/geneset/{biome}/{biome}_nr_rep_seq.fasta`
- `result/geneset/{biome}/{biome}_nr_cluster.tsv`
- `result/geneset/{biome}/{biome}_family_rep_seq.fasta`
- `result/geneset/{biome}/{biome}_family_cluster.tsv`

## Guardrails

- 95% 去冗余参数固定为 `--min-seq-id 0.95 -c 0.90 --cov-mode 1 --cluster-mode 3`
- 家族聚类参数固定为 `--min-seq-id 0.20 -c 0.50 --cov-mode 1 --cluster-mode 3`
- 运行时必须显式激活 MMseqs2 环境

## Examples

```bash
cd skills/metagenome-nonredundant-gene-sets
bash ./scripts/install_mmseqs2_env.sh \
  --env-prefix /home/{user_name}/software/conda-envs/metagenome-mmseqs2-14-7e28
bash ./scripts/run_mmseqs2_gene_sets.sh \
  --biome-list-dir /path/to/biome_list \
  --temp-root /path/to/temp \
  --output-root /path/to/result/geneset \
  --threads 20 \
  --conda-env-prefix /home/{user_name}/software/conda-envs/metagenome-mmseqs2-14-7e28
```
