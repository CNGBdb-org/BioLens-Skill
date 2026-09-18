---
name: ckb-meta-checkm2
description: >-
  MAG quality assessment using CheckM2. Evaluates completeness and contamination
  of metagenome-assembled genome bins from ckb-meta-binning using DIAMOND against
  UniRef100 KO database. Use for MAG quality filtering before taxonomy classification
  or pangenome analysis. Not for read-based QC (use ckb-meta-qc) or species profiling.
compatibility: "CheckM2 ≥1.0.1; DIAMOND ≥2.1; Python 3.10+; Linux x86_64; ≥16 GB RAM"
metadata:
  author: ckb-meta-team
  version: "1.0.0"
  scope: domain
  depth: L5
  domain: metagenomics
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
---

# ckb-meta-checkm2：MAG 质量评估

## Use When
- 需要评估 MAG bins 的完整度（completeness）和污染率（contamination）
- 输入来自 ckb-meta-binning 的 bin FASTA 文件

## Do Not Use When
| 需求 | 交给 |
|---|---|
| 原始 reads QC | ckb-meta-qc |
| MAG 物种分类 | ckb-meta-gtdbtk（在 checkm2 之后） |

## 软件依赖

```bash
# CheckM2
which checkm2 && checkm2 --version
# 要求：CheckM2 >= 1.0.1
# 安装：conda install -n base -c conda-forge -c bioconda -c defaults checkm2=1.0.1
#       或 pip install checkm2

# DIAMOND（CheckM2 内部依赖）
which diamond && diamond --version
# 要求：DIAMOND >= 2.1.0
# 安装：conda install -c bioconda diamond=2.1.0
```

## 数据库依赖

| 数据库 | 版本 | 大小 | DCS 路径 | 官方下载 |
|---|---|---|---|---|
| CheckM2 UniRef100 KO | v1.0 | ~2.8 GB | `/public/database/CKB_metagenome/checkm2/uniref100.KO.1.dmnd` | `checkm2 database --download --path /path/to/db` |

非 DCS 环境：
```bash
checkm2 database --download --path /path/to/checkm2_db
# 或手动下载：https://zenodo.org/records/5571251
export CHECKM2DB=/path/to/checkm2_db/uniref100.KO.1.dmnd
```

## Required Inputs

| 参数 | 说明 |
|---|---|
| bins_dir | MAG bins 目录（含多个 .fa 文件，来自 ckb-meta-binning）|
| sampleid | 样本 ID |
| db_path | uniref100.KO.1.dmnd 路径 |

## Workflow

**Gather**：确认 bins 目录非空、dmnd 数据库存在

**Act**：
```bash
checkm2 predict \
  --input {bins_dir} \
  --output-directory {sampleid}_checkm2_out \
  --database_path {db_path} \
  --threads 16 \
  -x fa
```

**DCS 平台**：投递 `CheckM_skill`

**Verify**：`cat {sampleid}_checkm2_out/quality_report.tsv | awk -F'\t' '$2>=50 && $3<=10' | wc -l` 查看高质量 MAG 数

## Output Contract

| 文件 | 说明 | 下游 |
|---|---|---|
| `{sampleid}_checkm2_out/quality_report.tsv` | 每个 bin 的 completeness / contamination | ckb-meta-gtdbtk（过滤后送入）|

## Guardrails

- 建议只将 completeness ≥50%、contamination ≤10% 的 MAG 传入 GTDB-Tk
- 不修改 bin FASTA 内容

## Errors and Fallback

| 错误 | 处理 |
|---|---|
| DIAMOND 找不到数据库 | 检查 db_path 是否为 .dmnd 文件 |
| 无有效 bin | bins_dir 为空或 bins 数量为 0，返回 ckb-meta-binning 检查 |

## Citation

- CheckM2: Chklovski et al., Nat Methods 2023. https://github.com/chklovski/CheckM2
