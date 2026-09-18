---
name: hcc-statistical-evidence-review
description: Review HCC multi-omics analysis plans and outputs for pairing errors, patient leakage, etiologic or background-liver confounding, inadequate statistical units, and overinterpretation. Use before releasing HCC findings or evaluating a proposed workflow.
tool_type: python
primary_tool: Manifest and evidence checks
---

# 统计与证据审查

先运行 `examples/evaluate_manifest.py`。它检查患者/样本重复、癌旁误标、无效配对等级和不支持患者级统计的缺失 ID。将检查结果写入报告；`fail` 时不得发布确定性结论。

进一步人工审查：事件数、协变量数量、训练/测试隔离、特征选择位置、外部验证、因果措辞和文献背景是否与本数据发现分开。
