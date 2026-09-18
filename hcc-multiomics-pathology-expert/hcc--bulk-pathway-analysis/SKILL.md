---
name: hcc-bulk-pathway-analysis
description: Analyze HCC bulk RNA expression with explicit normalization, design, pathway scoring, and effect-size reporting. Use when comparing HCC bulk RNA cohorts, evaluating pathways, or preparing bulk features for pathology associations.
tool_type: mixed
primary_tool: PyDESeq2 or compatible bulk RNA workflow
---

# HCC bulk RNA 与通路

确认输入是 counts、TPM/FPKM 还是已标准化矩阵，禁止混用。差异设计先列出患者、病因、背景肝、批次和临床协变量；样本不足时只做描述性或预设通路评分。

每个结果记录样本数、统计单位、效应量、置信区间或标准误、P 值、FDR、基因集来源和版本。v1 不执行突变、CNV 或甲基化的正式整合。
