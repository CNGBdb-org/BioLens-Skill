# 多切片空间配准


## 运行约定

```bash
cd skills/spatial/spatial-register
python ./scripts/query.py run <h5ad1> <h5ad2> [more...] [-o outdir]
```

内嵌：`scverse_common/`（本目录）

Align multiple spatial slices into a common coordinate frame (Procrustes on expression landmarks; PASTE if available). Use before spatial-integrate for multi-slice. Not for expression batch correction alone (use spatial-integrate).

## 示例问法

- 多切片配准
- 对齐两张 Visium 坐标
- spatial register Procrustes

## 命令

```bash
python ./scripts/query.py demo -o out/register
python ./scripts/query.py run s1.h5ad s2.h5ad -o out/register
```
