# 使用指南：空间 TME

适用于 Visium、Stereo-seq、SpatialData 和配套 H&E。典型顺序是空间 QC → 图像/坐标检查 → 聚类或程序评分 → 区域比较 → 患者级汇总。

10x Visium 基线路径不依赖 Scanpy：先运行 `examples/run_visium_qc.py`，再运行 `examples/analyze_spatial_domains.py`。它输出候选空间域及 HCC 程序分数；候选域不是病理边界，程序分数不是纯细胞类型。

GSE238264 仅用于 7 例 HCC 治疗响应空间路径回归：响应/非响应比较必须标为小样本探索性；若 H&E、比例尺或边界未提供，准确侵袭区和病理形态结论必须降级。
