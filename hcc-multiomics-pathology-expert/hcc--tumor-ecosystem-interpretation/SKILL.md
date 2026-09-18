---
name: hcc-tumor-ecosystem-interpretation
description: Interpret HCC malignant-hepatocyte, immune, vascular, fibroblast, and background-liver evidence across pathology and omics outputs. Use when translating HCC cell states or microenvironment results into cautious biological conclusions.
tool_type: mixed
primary_tool: Evidence synthesis
---

# HCC 肿瘤生态解释

整合已验证的输入，不替代上游 QC。恶性肝细胞至少需要两类独立支持：CNV、肿瘤相关程序、明确肿瘤区域、克隆/突变信息或可信来源标签。免疫、内皮和 CAF/星状细胞状态必须显示 marker/基因集、患者覆盖、置信度和反证。

将表达差异、空间邻近、通讯候选和因果验证分开。缺少背景肝或病因信息时，在任何肿瘤/癌旁结论上加混杂警告。

使用 `examples/synthesize_hcc_evidence.py` 只汇总空间摘要、H&E QC 和 bulk 基因集元数据中已存在的事实与限制。它不得生成诊断、恶性细胞定论或疗效结论。
