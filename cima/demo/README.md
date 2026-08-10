# CIMA pipeline demo data

## 配对多组学（推荐跑 Steps 1–6）

| File | Shape | 说明 |
|------|-------|------|
| `paired_demo_rna.h5ad` | 3001 × 2000 | scRNA（8 共同 sample，含 `counts`） |
| `paired_demo_atac.h5ad` | 2400 × 338036 | scATAC **peaks**（同 8 sample） |
| `paired_demo_atac_gene.h5ad` | 2400 × 1897 | scATAC **gene activity**（同细胞，供 Step5） |

RNA 与 ATAC **共享 8 个 donor**（`CIMA_H048`…），可做标签迁移 + metacell 配对。

跑通产物写到本地 `paired_run_out/`（已 gitignore，勿提交；图例在右侧，PNG + PDF）。

### 一键跑通（配对）

```bash
DEMO=cima/demo
OUT="$DEMO/paired_run_out"
SK=cima
mkdir -p "$OUT"

# 1 scRNA
cd $SK/cima-scrna-preprocessing
python ./scripts/cima_scrna_preprocessing_cpu.py \
  --input ../demo/paired_demo_rna.h5ad --output "$OUT/step1" \
  --hvg-n 1500 --sample-col sample --skip-subsampling

# 1b 无先验 cell type：L1 marker + 全基因矩阵（见下方脚本思路 / 已写入 paired_run_out）
# 产出: step1/CIMA_Annotation_1st_fullgenes.h5ad

# 2 L1–L4
cd ../cima-cell-annotation
python ./scripts/cima_cell_annotation_cpu.py \
  --input "$OUT/step1/CIMA_Annotation_1st_fullgenes.h5ad" \
  --output "$OUT/step2" --lineage all --skip-harmony --resolution 0.8

# 3 Pseudobulk
cd ../cima-pseudobulk-variance
python ./scripts/cima_pseudobulk_variance_cpu.py \
  --input "$OUT/step1/CIMA_Annotation_1st.h5ad" --output "$OUT/step3" \
  --sample-col sample --celltype-col celltype_1st --covariates age sex

# 4 scATAC peaks → gene activity（也可用现成 paired_demo_atac_gene）
cd ../cima-scratac-preprocessing
python ./scripts/cima_scratac_cpu.py \
  --input ../demo/paired_demo_atac.h5ad --output "$OUT/step4" \
  --skip-harmony --n-components 30 \
  --rna "$OUT/step1/CIMA_Annotation_1st_fullgenes.h5ad"

# 5 多组学：优先吃配对 gene ATAC
cd ../cima-multiomics-integration
python ./scripts/cima_multiomics_integration_cpu.py \
  --rna "$OUT/step1/CIMA_Annotation_1st_fullgenes.h5ad" \
  --atac ../demo/paired_demo_atac_gene.h5ad \
  --output "$OUT/step5" --n-hvg 800 --skip-harmony
# 或 --atac "$OUT/step4/CIMA_scATAC_gene_activity.h5ad"

# 6 Metacell（同 sample 时可配对）
cd ../cima-metacell
python ./scripts/cima_metacell_cpu.py \
  --rna "$OUT/step1/CIMA_Annotation_1st_fullgenes.h5ad" \
  --atac "$OUT/step5/CIMA_scATAC_Annotation_Transfered.h5ad" \
  --output "$OUT/step6" --celltype-col celltype_1st
```

### 期望结果摘要（配对）

| Step | 结果要点 |
|------|----------|
| 1 | ~3001 细胞；L1 粗标（常无先验 `cell_type`，靠 marker） |
| 2 | 按系群拆分后再标 L2–L4（本 demo 常无 myeloid → 仅 B + TNK） |
| 3 | sample×celltype pseudobulk + age/sex 方差分解 |
| 4 | peaks 聚类；可选写出 `CIMA_scATAC_gene_activity.h5ad` |
| 5 | 共同基因上整合；ATAC 标签迁移 |
| 6 | 同 sample 时 RNA–ATAC metacell **可配对**（本次约 40 pairs） |

---

## 其它 demo（非配对 / 更小）

| File | 说明 |
|------|------|
| `demo_nk_raw.h5ad` | 3000×1000 RNA，与 ATAC **样本不重叠** |
| `demo_atac_raw.h5ad` | 1000×2000 peaks，单 sample |

非配对跑通时 Step6 配对为 0。产物目录 `run_out/` 已 gitignore。

GRN / xQTL / SMR / Resource / CLM 不依赖本目录 h5ad。数据清单与 FTP 位置用 `cima-resource`。
