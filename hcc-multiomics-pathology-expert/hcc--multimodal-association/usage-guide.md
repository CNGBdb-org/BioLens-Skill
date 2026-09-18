# 使用指南：跨模态关联

适用于“病理形态与缺氧/血管生成/免疫通路是否相关”。优先从患者级聚合开始；若只有单张切片或没有可靠配对，交付局部描述与假设，不交付群体推断。

对 Visium + 同切片 H&E，先完成空间域、H&E QC 与切片 tile，再运行：

```powershell
python examples/link_visium_spots_to_he_tiles.py --spatial-domains <run>/spatial/spatial_domains.tsv --he-tiles <run>/pathology_tiles/he_tile_coordinates.tsv --scalefactors <sample>/spatial/scalefactors_json.json --output <run>/multimodal
```

读取 `visium_he_tile_links.tsv` 取得 spot-to-tile 证据，读取 `he_tile_spatial_evidence.tsv` 获取每个 tile 的候选域和程序均值。缺失坐标或不同图像坐标系时必须停止链接，并写明阻断原因。
