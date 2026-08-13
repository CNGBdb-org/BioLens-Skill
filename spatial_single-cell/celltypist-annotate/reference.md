# CellTypist 注释 — 解读路径

## 输入 → 输出

- 输入：log1p normalize（target_sum=1e4）后的 scRNA `h5ad`；基因名通常为 symbol
- 输出：`report.md` + `tables/`（predicted_labels / decision / probability）+ `figures/` + `celltypist_annotated.h5ad`

## 依赖

- 必需：`celltypist`、scanpy、anndata、matplotlib、pandas、numpy
- 模型缓存：默认 `~/.celltypist/`（可用环境变量 `CELLTYPIST_FOLDER`）
- 首次下载需访问 `https://celltypist.cog.sanger.ac.uk`

## 模型选择（摘要）

| 场景 | 建议模型 |
|------|----------|
| 跨组织免疫 / PBMC（细粒度） | `Immune_All_Low.pkl`（默认） |
| 跨组织免疫（粗粒度） | `Immune_All_High.pkl` |
| 成人肝 / 肺 / 皮肤 / 心 等 | 对应 `Healthy_Human_*` / `Cells_*` / `Human_*` 组织模型 |
| 发育 / 胎儿组织 | `Developing_*` / `Fetal_*` / `Pan_Fetal_Human.pkl` |

完整列表：`python ./scripts/query.py models` 或 https://www.celltypist.org/models

## 注意

- 本 skill 做注释编排，不负责 GEO 下载（用 `geo-sra`）与 CIMA 本体（用 `cima-cell-annotation`）
- `majority_voting=True` 更稳但更慢；已有 `leiden` 时可 `--over-clustering leiden`
- v1 不做 `celltypist.train` 自定义训练
