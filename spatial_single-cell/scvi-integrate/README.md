# scVI 整合（可降级）


## 运行约定

```bash
cd skills/single-cell/scvi-integrate
python ./scripts/query.py <args>  # 见 README
```

内嵌：`scverse_common/`（本目录）

Integrate scRNA batches with scvi-tools SCVI when installed; otherwise fall back to Scanpy Combat/PCA. Use for deep generative batch correction.

## 示例问法

- 帮我跑一下 scVI 整合（可降级）
- 输入我的 h5ad，输出报告和图

## 命令

```bash
python ./scripts/query.py <h5ad> -o out/scvi_integrate
```
