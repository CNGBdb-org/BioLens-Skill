---
name: cima-clm
description: >-
  CIMA-CLM in silico mutagenesis demo: visualize Enformer-based variant effects on
  gene expression from pre-computed predictions (no GPU/weights). Use for CLM demo
  heatmaps/line charts/sequence logos. Not for live Enformer inference, ClinVar
  pathogenicity (use clinvar), gnomAD AF (use gnomad), or CIMA portal xQTL/SMR
  tables (use cima).
compatibility: Python 3.10+, pandas, numpy, matplotlib, seaborn; optional logomaker
metadata:
  author: cngbdb-skill-team
  version: "2.0.0"
  scope: database-unique
  depth: L5
  domain: single-cell
  capability_id: cngbdb.cima.clm-demo.v1
  load_strategy: database-on-demand
  status: beta
  quality: Q3
  databases: [cima]
---

# CIMA-CLM Variant Effect Demo

CIMA 流水线 Step 10（L5）：基于**预计算** Enformer 结果的 in silico mutagenesis 可视化。**必须**调用包内脚本。Demo 数据不随 Skill 打包，需本地 `CIMA-CLM_Demo` 目录或 `CIMA_CLM_DEMO`。

## Use When

- 运行 CIMA-CLM demo（热图 / 折线 / sequence logo）
- 仅有预计算结果、无 GPU / 模型权重

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 临床致病性 | `clinvar` |
| 人群频率 | `gnomad` |
| 门户 xQTL / SMR 表 | `cima` |
| 全量 Enformer 重算 | 超出本 Skill（需 GPU + 权重） |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据 | `CIMA-CLM_Demo` 下预计算 CSV |
| 能力边界 | 可视化 demo，非生产级变异评分服务 |

## Required inputs

| 输入 | 必填 | 说明 |
|------|------|------|
| `data_dir` | 是 | `CIMA-CLM_Demo` 路径，或环境变量 `CIMA_CLM_DEMO` |
| `--out` | 否 | 输出目录（默认 `<data_dir>/output`） |

期望数据文件（示例）：

- `Switched_Bm_IGHDnegchr22_39351775_150bp.csv`
- `Switched_Bm_IGHDneg_silicon_results.csv`

## Necessary questions

1. 未提供 Demo 数据路径 → 补问路径或 `CIMA_CLM_DEMO`  
2. 用户要实时模型推理 → 说明本 Skill 仅预计算 demo  

## Workflow

1. **Gather**：确认 Demo 目录存在且含预计算 CSV  
2. **Act**：只跑 `./scripts/run_demo.py`  
3. **Verify**：检查输出 CSV / PDF；不编造效应值  

## Commands

```bash
# 指定 Demo 数据目录
python ./scripts/run_demo.py /path/to/CIMA-CLM_Demo

# 或使用环境变量
export CIMA_CLM_DEMO=/path/to/CIMA-CLM_Demo
python ./scripts/run_demo.py --out ./my_results
```

## Output contract

- 变异展开 CSV、均值效应表
- `heatmap.pdf` / `linechart.pdf` / `seq_logo.pdf`（logomaker 可选）

## Guardrails

- 禁止使用绝对机器路径（如 `/home/...`、`/work/...`）
- 禁止在无脚本输出时虚构预测分数
- 明确标注结果来自预计算，非现场推理

## Errors and fallback

- 未给 `data_dir` → 退出并提示参数 / 环境变量
- 缺 CSV → 列出缺失文件
- 无 logomaker → 跳过 sequence logo 并说明

## Examples

**用户**：跑一下 CIMA-CLM demo，出热图和折线图  

```bash
cd skills/cima/cima-clm
# 方式 A：传 Demo 目录
python ./scripts/run_demo.py /path/to/CIMA-CLM_Demo --out ./clm_out

# 方式 B：环境变量
export CIMA_CLM_DEMO=/path/to/CIMA-CLM_Demo
python ./scripts/run_demo.py --out ./clm_out
```

**产出**：变异效应表、`heatmap.pdf`、`linechart.pdf`（可选 `seq_logo.pdf`）

## Citation

CIMA / TrueBlood — Yin et al., Science 2026; DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)
