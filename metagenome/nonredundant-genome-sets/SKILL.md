---
name: metagenome-nonredundant-genome-sets
description: >-
  Metagenomic pipeline Step 9 dereplication and taxonomic classification of MAGs
  using GTDB-Tk v2.3.2 and dRep v3.3.0, followed by ORF prediction with Prodigal
  v2.6.3 and DIAMOND-based COG/KEGG annotation.
compatibility: Bash, conda, GTDB-Tk v2.3.2, dRep v3.3.0, Prodigal v2.6.3, DIAMOND v2.1.6
---

# Metagenome Non-redundant Genome Sets

宏基因组流程 Step 9：对同一环境类别的 MAG 去冗余，进行 GTDB-Tk 分类，随后预测 MAG ORF，并用 DIAMOND 做 COG 与 KEGG 注释。


## 文件与目录规范
所有生成的脚本和分析产物**不得放在 skills 目录下**。每次使用本 Skill 时，先在项目根目录（skills 同级）创建 outdir 结构：
```bash
PROJ_ROOT=$(dirname "$(dirname "$SKILLS_DIR")")   # skills 所在目录的上级
SKILL_OUTDIR="$PROJ_ROOT/outdir/metagenome-nonredundant-genome-sets"
mkdir -p "$SKILL_OUTDIR/script"    # 生成的运行脚本
mkdir -p "$SKILL_OUTDIR/prosess"   # 分析中间文件
mkdir -p "$SKILL_OUTDIR/result"    # 最终结果文件
```
- script/   — 本次生成的运行脚本（如 nonredundant-genome-sets_run_<date>.sh）
- prosess/  — 分析中间文件、临时目录
- result/   — 最终结果文件
## Software environment

- 推荐环境名：`metagenome-mag-stack`
- 推荐环境前缀：`/home/{user_name}/software/conda-envs/metagenome-mag-stack`
- 安装脚本：`./scripts/install_mag_env.sh`
- 运行脚本：`./scripts/run_nr_genome_sets.sh`

## Guardrails

- dRep 参数固定为 `--length 0 --completeness 50 --contamination 10 --S_algorithm ANImf --P_ani 0.9 --S_ani 0.95 --cov_thresh 0.3 --strain_heterogeneity_weight 0`
- GTDB-Tk 固定 `classify_wf --skip_ani_screen`
- Prodigal 使用默认参数
- COG/KEGG 注释使用 DIAMOND `blastp -e 0.00001`
