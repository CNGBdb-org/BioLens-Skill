# 空间拟时序 / 轨迹


## 运行约定

```bash
cd skills/spatial/spatial-trajectory
python ./scripts/query.py <h5ad> [-o outdir] [--root CELL_ID]
```

内嵌：`scverse_common/`（本目录）

Compute diffusion pseudotime (DPT) or PCA-rank fallback on spatial AnnData and plot spatial trajectory. Use for differentiation/ordering along tissue. Not for multi-slice registration (use spatial-register) or SVG (use spatial-svg).

## 示例问法

- 空间拟时序
- DPT 轨迹画在组织上
- spatial trajectory

## 命令

```bash
python ./scripts/query.py spatial.h5ad -o out/traj
python ./scripts/query.py --demo -o out/traj_demo
```
