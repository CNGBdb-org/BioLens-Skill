---
name: hcc-evidence-reporting
description: Generate research-use HCC multi-omics evidence reports with provenance, evidence levels, limitations, and navigable result links. Use when delivering HCC pathology or omics findings to a researcher.
tool_type: python
primary_tool: Structured report generation
---

# HCC 证据报告

运行 `examples/build_results_index.py` 生成结果入口。报告必须分别说明数据发现、方法、统计单位、配对等级、证据、限制和不能推出的结论。为每条关键结论链接到原始产物、证据区域或表格。

报告顶部固定写明“仅用于科研分析，需领域专家复核，不用于临床诊断或治疗决策”。不能因部分分支失败而隐藏失败状态。
