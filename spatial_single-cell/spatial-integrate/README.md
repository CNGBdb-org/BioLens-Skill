# 多样本空间整合


## 运行约定

```bash
cd skills/spatial/spatial-integrate
python ./scripts/query.py <h5ad> [-o outdir] [--batch-key batch]
```

内嵌：`scverse_common/`（本目录）

Integrate multi-sample spatial AnnData (Harmony if installed else Combat/PCA). Needs obs batch or slice. Use after spatial-register or concat. Not for coordinate alignment (use spatial-register) or scRNA-only integrate (use sc-multi-integrate / scvi-integrate).

## 示例问法

- 多样本空间整合
- Harmony 整合 Visium
- spatial integrate

## 命令

```bash
python ./scripts/query.py multi.h5ad -o out/integ --batch-key slice
python ./scripts/query.py --demo -o out/integ_demo
```
