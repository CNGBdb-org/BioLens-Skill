---
name: hcc-pathology-qc-evidence
description: Perform research-use HCC WSI or H&E quality checks, tissue-aware tiling, coordinate recording, and pathology evidence retrieval. Use when inspecting HCC slides, extracting reproducible patches, or linking molecular findings back to image regions.
tool_type: mixed
primary_tool: OpenSlide-compatible reader
---

# HCC 病理 QC 与证据回溯

先确认 `slide_id`、图像格式、倍率或 MPP、组织来源和关联患者。输出缩略图、QC 指标、组织区域、patch 坐标与可回溯证据清单。

默认只做组织/背景检测和候选区域；肿瘤边界优先采用病理专家 ROI。没有标注集时不得报告自动肿瘤分割准确率，也不得做临床分级或诊断。

核心路径使用可商用许可的 reader 和传统 QC。TRIDENT、HEST 或基础模型权重必须在运行前单独核验许可并标为 `research-only`。
