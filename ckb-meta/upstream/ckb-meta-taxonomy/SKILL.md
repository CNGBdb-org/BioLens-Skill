---
name: ckb-meta-taxonomy
description: >-
  Read-based taxonomic profiling of metagenomics samples using MetaPhlAn4.
  Takes rmhost FASTQ (paired-end) from ckb-meta-qc, outputs per-sample species
  abundance profile (.mp4.profile) and marker consensus pickle (.pkl) for
  StrainPhlAn4. Use for species composition profiling of gut microbiome. Not
  for assembly-based MAG taxonomy (use ckb-meta-gtdbtk), or functional annotation
  (use ckb-meta-humann).
compatibility: "MetaPhlAn4 ≥4.1; bowtie2 ≥2.4.5; Python 3.10+; Linux x86_64; ≥32 GB RAM"
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

# ckb-meta-taxonomy：MetaPhlAn4 物种注释

## Use When
- 需要 read-based 物种组成 profile（属/种/株水平）
- 输入来自 ckb-meta-qc 的 rmhost FASTQ
- 需要为 ckb-meta-strainphlan 生成 .pkl 文件

## Do Not Use When
| 需求 | 交给 |
|---|---|
| MAG 分类（assembly-based） | ckb-meta-gtdbtk |
| 功能注释 | ckb-meta-humann（内部已含 MetaPhlAn 步骤）|
| 已有 profile，需要合并 | ckb-meta-merge |

## 软件依赖

```bash
# MetaPhlAn4
which metaphlan && metaphlan --version
# 要求：MetaPhlAn >= 4.1.0
# 安装：conda install -c biobakery metaphlan=4.1.0
#       或 pip install metaphlan

# bowtie2（MetaPhlAn 内部依赖）
which bowtie2 && bowtie2 --version
# 要求：>= 2.4.5
```

## 数据库依赖

| 数据库 | 版本 | 大小 | DCS 路径 | 官方下载 |
|---|---|---|---|---|
| MetaPhlAn4 SGB 数据库 | mpa_vOct22_CHOCOPhlAnSGB_202212 | ~46 GB（含 Bowtie2 索引） | `/public/database/CKB_metagenome/metaphlan/` | `metaphlan --install --bowtie2db /your/db/path` |

非 DCS 环境：
```bash
# 方法一：metaphlan 自动下载
metaphlan --install --bowtie2db /path/to/metaphlan_db --index mpa_vOct22_CHOCOPhlAnSGB_202212

# 方法二：手动下载
# https://zenodo.org/records/7952755 → mpa_vOct22_CHOCOPhlAnSGB_202212_bt2.tar
# 解压后设置：
export MPA_DB=/path/to/metaphlan_db
```

## Required Inputs

| 参数 | 说明 |
|---|---|
| rmhost1 | rmhost R1 FASTQ.gz（ckb-meta-qc 输出） |
| rmhost2 | rmhost R2 FASTQ.gz（ckb-meta-qc 输出） |
| sampleid | 样本 ID |
| bowtie2db | MetaPhlAn Bowtie2 数据库目录路径 |
| index | 数据库索引名（默认 mpa_vOct22_CHOCOPhlAnSGB_202212） |

## Workflow

**Gather**：确认 rmhost FASTQ 路径、数据库路径

**Act**：
```bash
# 合并双端 reads 输入 MetaPhlAn4
metaphlan \
  {rmhost1},{rmhost2} \
  --bowtie2db {bowtie2db} \
  --index {index} \
  --input_type fastq \
  --nproc 8 \
  --sample_id {sampleid} \
  --bowtie2out {sampleid}.mp4.bw2.bz2 \
  -s {sampleid}.sam.bz2 \
  -o {sampleid}.mp4.profile \
  2>{sampleid}.metaphlan4.log

# 生成 pkl（供 strainphlan 使用）
sample2markers.py \
  -i {sampleid}.sam.bz2 \
  -d {bowtie2db}/{index}.pkl \
  -o ./ \
  -n 8
```

**DCS 平台**：投递 `metaphlan4_skill`

**Verify**：`wc -l {sampleid}.mp4.profile` 应 >10；`ls {sampleid}.pkl` 存在

## Output Contract

| 文件 | 说明 | 下游 |
|---|---|---|
| `{sampleid}.mp4.profile` | 物种丰度表（各分类层级） | ckb-meta-merge（物种 profile 合并）|
| `{sampleid}.pkl` | Marker consensus pickle | ckb-meta-strainphlan |
| `{sampleid}.mp4.bw2.bz2` | Bowtie2 比对结果 | - |

## Guardrails

- 不跳过数据库检测直接运行
- profile 必须过滤到 s__ species 层后再进入 downstream 统计

## Errors and Fallback

| 错误 | 处理 |
|---|---|
| 数据库路径找不到 | 检查 bowtie2db 下是否有 .bt2l 文件 |
| profile 全为 UNKNOWN | reads 质量差或测序深度不足（<1M reads）|

## Citation

- MetaPhlAn4: Blanco-Míguez et al., Nat Methods 2023. https://github.com/biobakery/MetaPhlAn
- Database: https://zenodo.org/records/7952755
