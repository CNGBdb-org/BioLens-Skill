---
name: hcc-spatial-tme-analysis
description: Analyze HCC spatial-transcriptomic quality, region-aware programs, microenvironment patterns, and histology alignment. Use when working with HCC Visium, Stereo-seq, SpatialData, or spatial H&E-associated expression data.
tool_type: mixed
primary_tool: Scanpy and Squidpy-compatible workflow
---

# HCC 空间 TME 分析

先验证表达矩阵、坐标、比例尺、图像和边界是否在同一坐标系。无人工边界时可输出候选区域或无监督空间结构，但不得将其称为病理级肿瘤核心、边缘或侵袭区。

spot 不是独立患者。所有组间推断先在患者内汇总，再以患者为统计单位。无 scRNA 参考时可报告 marker/通路，不把 spot 直接命名为纯细胞类型。
