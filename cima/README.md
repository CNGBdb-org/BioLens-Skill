# CIMA Pipeline Skills

CIMA / TrueBlood **本地流水线与独立查询 Skill**，路径：`cima/<name>/`。本目录共 **12** 个 Skill。

| Skill | Depth | 用途 |
|-------|-------|------|
| `cima-resource` | L3 | CIMA 数据清单 / 本地路径（部署：`/public/.../CIMA_Resource`；外网门户·FTP） |
| `cima-atlas-explore` | L4 | 门户图谱浏览：视图 / donor / 组成 / 基因 UMAP（不含 GRN·xQTL·SMR·清单） |
| `cima-scrna-preprocessing` | L5 | scRNA QC → 聚类 → 系群拆分 |
| `cima-cell-annotation` | L5 | TrueBlood marker 签名 → L1–L4（73 leaf） |
| `cima-pseudobulk-variance` | L5 | Pseudobulk 聚合 + 方差分解 |
| `cima-scratac-preprocessing` | L5 | scATAC peak 预处理 + 可选 gene activity（CPU） |
| `cima-multiomics-integration` | L5 | scRNA+scATAC 整合（ATAC 可为 peak 或 gene） |
| `cima-metacell` | L5 | Metacell 聚合（CPU，无 SEACells） |
| `cima-grn-scenicplus` | L4 | 预计算 eRegulon / GRN 查询（独立，不依赖 explore `cima`） |
| `cima-xqtl` | L4 | 预计算 cis-xQTL 查询（独立） |
| `cima-smr-gwas` | L4 | 预计算 SMR/GWAS 查询（独立） |
| `cima-clm` | L5 | CLM in silico 变异效应 demo（预计算结果） |

## 流水线关系

- 图谱浏览：`cima-atlas-explore`（视图 / donor / UMAP；清单与 GRN/xQTL/SMR 见专用 Skill）
- scRNA 主线：`cima-scrna-preprocessing` → `cima-cell-annotation` → `cima-pseudobulk-variance` → `cima-xqtl` / `cima-smr-gwas`
- 多组学主线：… → `cima-scratac-preprocessing` → `cima-multiomics-integration` → `cima-metacell` → `cima-grn-scenicplus`
- 独立：`cima-resource`、`cima-clm`

## 安装

见仓库根目录 [README.md · 安装方式](../README.md#安装方式)：

```bash
./install-to-agent.sh --agent cursor --category cima
./install-to-agent.sh --agent cursor --global --category cima
```

安装后形态：`<skills-dir>/<skill-name>/SKILL.md`。

## 使用示例

每个 Skill 的 `SKILL.md` 均有 **Examples**。本目录提供合成 demo（仅冒烟，非论文复现）：

| 文件 | 用途 |
|------|------|
| [`demo/paired_demo_rna.h5ad`](demo/paired_demo_rna.h5ad) | **推荐** scRNA（与 ATAC 共享 8 donor）→ Steps 1–3 / 5–6 |
| [`demo/paired_demo_atac.h5ad`](demo/paired_demo_atac.h5ad) | **推荐** scATAC peaks → Step 4（可出 gene activity） |
| [`demo/paired_demo_atac_gene.h5ad`](demo/paired_demo_atac_gene.h5ad) | **推荐** gene-level ATAC → 直喂 Step 5 |
| `demo/demo_nk_raw.h5ad` + `demo/demo_atac_raw.h5ad` | 更小；样本不重叠 → Step6 配对为 0 |

完整 Steps 1–6 命令见 [`demo/README.md`](demo/README.md)。下面是命令速查（路径相对叶子 Skill，demo 在 `../demo/`）。

| Skill | 一键示例 |
|-------|----------|
| `cima-resource` | `python ./scripts/cima_resource_lookup.py overview` |
| `cima-atlas-explore` | `python ./scripts/query.py catalog list_datasets` |
| `cima-scrna-preprocessing` | `python ./scripts/cima_scrna_preprocessing_cpu.py --input ../demo/paired_demo_rna.h5ad --output ./out --hvg-n 1500 --skip-subsampling` |
| `cima-cell-annotation` | `python ./scripts/cima_cell_annotation_cpu.py --input Annotation_1st_fullgenes.h5ad --output ./out --lineage all` |
| `cima-pseudobulk-variance` | `python ./scripts/cima_pseudobulk_variance_cpu.py --input Annotation_1st.h5ad --output ./out --covariates age sex` |
| `cima-scratac-preprocessing` | `python ./scripts/cima_scratac_cpu.py --input ../demo/paired_demo_atac.h5ad --output ./out --rna rna.h5ad` |
| `cima-multiomics-integration` | `python ./scripts/cima_multiomics_integration_cpu.py --rna rna.h5ad --atac ../demo/paired_demo_atac_gene.h5ad --output ./out` |
| `cima-metacell` | `python ./scripts/cima_metacell_cpu.py --rna rna.h5ad --atac atac_labeled.h5ad --output ./out` |
| `cima-grn-scenicplus` | `bash ./scripts/grn.sh grn_lookup --tf FOXP3 --max 20` |
| `cima-xqtl` | `bash ./scripts/xqtl.sh --gene CDC42 --max 20` |
| `cima-smr-gwas` | `bash ./scripts/smr.sh --gene ARL14EP --max 10` |
| `cima-clm` | `python ./scripts/run_demo.py /path/to/CIMA-CLM_Demo --out ./clm_out` |

### Agent 侧怎么触发（自然语言示例）

| # | 用户说法（示例） | 触发 Skill |
|---|------------------|------------|
| 0 | CIMA 有哪些数据？在哪？/ TrueBlood resource 本地路径 / NK h5ad 在哪 | `cima-resource` |
| 0b | CIMA 有哪些视图？/ B 视图画 CD8A UMAP / donor 临床表 | `cima-atlas-explore` |
| 1 | 按 CIMA 流程预处理这个 PBMC h5ad / 对 raw counts 做 QC 聚类再按系群拆分 | `cima-scrna-preprocessing` |
| 2 | 对 CIMA Annotation_1st 做系群子聚类 + L1–L4 marker 签名注释 | `cima-cell-annotation` |
| 3 | 按 sample×celltype 做 pseudobulk，看看 age/sex 各解释多少方差 | `cima-pseudobulk-variance` |
| 4 | 没有 GPU，用 CPU 预处理这个 scATAC peak 矩阵 | `cima-scratac-preprocessing` |
| 5 | 把 scRNA 的细胞类型迁到 scATAC（不用 SCGLUE） | `cima-multiomics-integration` |
| 6 | SEACells 装不了，用 CPU 做 CIMA metacell | `cima-metacell` |
| 7 | FOXP3 在 CIMA 里调控哪些基因？/ 列一下 B 系群 eRegulon | `cima-grn-scenicplus` |
| 8 | 查 CDC42 的 cis-eQTL / Bn_TCL1A 的 cis-caQTL | `cima-xqtl` |
| 9 | ARL14EP（或某基因）在 CIMA SMR 里有哪些免疫疾病关联？ | `cima-smr-gwas` |
| 10 | 跑一下 CIMA-CLM in silico mutagenesis demo | `cima-clm` |
