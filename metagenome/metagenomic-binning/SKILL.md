---
name: metagenome-metagenomic-binning
description: >-
  Metagenomic pipeline Step 8 MAG recovery from metagenomes using MetaWRAP v1.3
  binning with --metabat2 -l 1000 and quality assessment by CheckM v1.2.2
  lineage_wf. Retains bins with completeness >=50% and contamination <10%.
compatibility: Bash, conda, MetaWRAP v1.3, CheckM v1.2.2
---

# Metagenome Binning

宏基因组流程 Step 8：使用 MetaWRAP 的 binning 模块进行 MAG 恢复，随后用 CheckM 评估 completeness 与 contamination，并保留 completeness ≥ 50%、contamination < 10% 的 bins。


## 文件与目录规范
所有生成的脚本和分析产物**不得放在 skills 目录下**。每次使用本 Skill 时，先在项目根目录（skills 同级）创建 outdir 结构：
```bash
PROJ_ROOT=$(dirname "$(dirname "$SKILLS_DIR")")   # skills 所在目录的上级
SKILL_OUTDIR="$PROJ_ROOT/outdir/metagenome-metagenomic-binning"
mkdir -p "$SKILL_OUTDIR/script"    # 生成的运行脚本
mkdir -p "$SKILL_OUTDIR/prosess"   # 分析中间文件
mkdir -p "$SKILL_OUTDIR/result"    # 最终结果文件
```
- script/   — 本次生成的运行脚本（如 metagenomic-binning_run_<date>.sh）
- prosess/  — 分析中间文件、临时目录
- result/   — 最终结果文件
## Software environment

- 推荐环境名：`metagenome-binning-stack`
- 推荐环境前缀：`/home/{user_name}/software/conda-envs/metagenome-binning-stack`
- 安装脚本：`./scripts/install_binning_env.sh`
- 运行脚本：`./scripts/run_metawrap_binning.sh`

## Guardrails

- MetaWRAP 固定关键参数：`--metabat2 -l 1000`
- CheckM 使用 `lineage_wf` 默认参数
- 质控阈值固定：completeness ≥ 50%，contamination < 10%

## Examples

```bash
cd skills/metagenome-metagenomic-binning
bash ./scripts/install_binning_env.sh \
  --env-prefix /home/{user_name}/software/conda-envs/metagenome-binning-stack
bash ./scripts/run_metawrap_binning.sh \
  --sample-list /path/to/sample.txt \
  --temp-root /path/to/temp \
  --threads 10 \
  --conda-env-prefix /home/{user_name}/software/conda-envs/metagenome-binning-stack
```
