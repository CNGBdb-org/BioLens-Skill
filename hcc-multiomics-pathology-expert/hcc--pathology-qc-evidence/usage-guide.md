# 使用指南：病理 QC 与证据

适用于“检查这批 WSI”“把 RNA 通路结果定位到切片”“提取可复跑 patch”。先完成数据接入；再记录 MPP、目标倍率、patch 尺寸、坐标系和 mask 来源。

对于 PNG/JPG 等已渲染 H&E（包括 Visium 的 `tissue_hires_image.png`），先运行：

```powershell
python examples/run_he_qc.py --image <he-image> --slide-id <slide-id> --output <run>/pathology_qc
python examples/tile_he_image.py --image <he-image> --mask <run>/pathology_qc/tissue_mask.png --slide-id <slide-id> --output <run>/pathology_tiles --write-patches
```

输出 `he_qc_summary.json`、缩略图、传统组织掩膜和带原始像素坐标的 `he_tile_coordinates.tsv`。这是可追溯图像证据的起点，不代表肿瘤区域、坏死区域或病理诊断。SVS/NDPI 等 WSI 须在本机配置 OpenSlide 后，保留 MPP/level，并沿用相同的坐标字段。

每个证据 patch 至少包含 `slide_id`、`x`、`y`、`level_or_mpp`、`patch_size`、`selection_reason`。没有 WSI/H&E 时将病理分支标为阻断，不用空间坐标代替切片图像。
