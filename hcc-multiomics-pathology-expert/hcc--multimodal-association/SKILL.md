---
name: hcc-multimodal-association
description: Associate HCC pathology features, spatial programs, single-cell outputs, and bulk RNA at the documented pairing level. Use when testing pathology-to-omics or cross-modal HCC associations.
tool_type: mixed
primary_tool: Patient-level association workflow
---

# HCC 跨模态关联

先读取配对矩阵。所有结果表必须显示 `pairing_level`；未证明同一组织块的 TCGA WSI 与 RNA 仅可做患者级关联。先报告单模态质量和临床/病因基线，再报告跨模态关联。

对同一张 Visium H&E 渲染图，用 `examples/link_visium_spots_to_he_tiles.py` 将 spot 中心投射到病理 QC 生成的 H&E tile。必须显式传入 `scalefactors_json.json` 并记录坐标框架；此链接仅用于证据索引，不能作为细胞共定位或病理诊断。

特征选择、标准化和调参只能在训练折内完成。小样本不使用“临床预测”措辞；证据区域只能解释为与统计关联相符的候选形态位置。
