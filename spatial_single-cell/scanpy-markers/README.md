# Scanpy Marker 基因


## 运行约定

```bash
cd skills/single-cell/scanpy-markers
python ./scripts/query.py <h5ad> [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Rank marker genes per cluster with Scanpy wilcoxon. Use after clustering to find cluster markers.

## 示例问法

- 帮我跑一下 Scanpy Marker 基因
- 输入我的 h5ad，输出报告和图

## 命令

```bash
python ./scripts/query.py <h5ad> -o out/scanpy_markers
```
