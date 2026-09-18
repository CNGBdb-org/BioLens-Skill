---
name: hcc-scrna-coordination
description: Create and validate explicit handoffs from HCC multi-omics work to the DCS scRNA-seq expert, then consume returned annotations for HCC interpretation. Use when an HCC task needs general single-cell loading, QC, integration, clustering, annotation, or communication analysis.
tool_type: python
primary_tool: DCS Expert handoff contract
---

# HCC 单细胞协同

不要复制 `scrna-seq-expert` 的数据读写、QC、整合、聚类、marker、自动注释和通讯实现。先运行 `examples/create_handoff.py`，目标 Expert 固定为 `scrna-seq-expert`，并明确所需子 Skill、输入路径、物种、组织、分析目标和预期返回字段。

返回结果必须包含处理后对象路径、`cell_type`、`sample_id`、`patient_id`、注释证据/置信度和方法版本；否则阻断 HCC 特异解释。恶性肝细胞判断由本 Expert 的生态解释 Skill 执行，且需至少两类独立证据。
