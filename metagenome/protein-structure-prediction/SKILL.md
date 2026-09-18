---
name: metagenome-protein-structure-prediction
description: >-
  Metagenomic pipeline Step 7 representative protein structure-set construction.
  Retains protein-family clusters with >30 members, ranks complete CDS-derived
  sequences against centroid by BLASTP v2.16.0, predicts top candidates by ESMFold,
  and selects representative structures using pTM.
compatibility: Bash, Python 3, conda, BLAST+ v2.16.0, ESMFold
---

# Metagenome Protein Structure Prediction

宏基因组流程 Step 7：基于蛋白家族聚类结果筛选成员数大于 30 的 cluster，使用 BLASTP 将 complete CDS 蛋白比对到中心序列，选择得分最高的候选序列做 ESMFold 结构预测，并按 pTM 选代表结构。


## 文件与目录规范
所有生成的脚本和分析产物**不得放在 skills 目录下**。每次使用本 Skill 时，先在项目根目录（skills 同级）创建 outdir 结构：
```bash
PROJ_ROOT=$(dirname "$(dirname "$SKILLS_DIR")")   # skills 所在目录的上级
SKILL_OUTDIR="$PROJ_ROOT/outdir/metagenome-protein-structure-prediction"
mkdir -p "$SKILL_OUTDIR/script"    # 生成的运行脚本
mkdir -p "$SKILL_OUTDIR/prosess"   # 分析中间文件
mkdir -p "$SKILL_OUTDIR/result"    # 最终结果文件
```
- script/   — 本次生成的运行脚本（如 protein-structure-prediction_run_<date>.sh）
- prosess/  — 分析中间文件、临时目录
- result/   — 最终结果文件
## Use When

- 已完成 MMseqs2 家族聚类
- 已保留 complete CDS 对应蛋白序列
- 需要构建 habitat 级代表蛋白结构集及按 pLDDT/pTM 分类置信度

## Software environment

- BLAST 推荐环境名：`metagenome-blast-2.16.0`
- ESMFold 推荐环境名：`metagenome-esmfold`
- 安装脚本：`./scripts/install_structure_env.sh`
- 运行脚本：`./scripts/run_structure_prediction.sh`

## Required inputs

| 参数 | 必填 | 说明 |
|------|------|------|
| `--geneset-root` | 是 | `result/geneset/` 根目录 |
| `--temp-root` | 是 | `temp/` 根目录 |
| `--output-root` | 是 | 结构输出根目录 |
| `--blast-env-name / --blast-env-prefix` | 否 | BLAST conda 环境 |
| `--esmfold-cmd` | 是 | ESMFold 可执行命令或脚本路径 |

## Guardrails

- 仅保留 cluster 成员数 > 30 的蛋白家族
- BLASTP 参数固定为 `-outfmt 6 -max_hsps 1 -max_target_seqs 3`
- 仅使用 complete CDS 蛋白参与代表结构候选筛选
- 高置信度/良好置信度/低置信度按 pLDDT 与 pTM 阈值分类

## Examples

```bash
cd skills/metagenome-protein-structure-prediction
bash ./scripts/install_structure_env.sh \
  --blast-env-prefix /home/{user_name}/software/conda-envs/metagenome-blast-2.16.0
bash ./scripts/run_structure_prediction.sh \
  --geneset-root /path/to/result/geneset \
  --temp-root /path/to/temp \
  --output-root /path/to/result/structureset \
  --blast-env-prefix /home/{user_name}/software/conda-envs/metagenome-blast-2.16.0 \
  --esmfold-cmd esm-fold
```
