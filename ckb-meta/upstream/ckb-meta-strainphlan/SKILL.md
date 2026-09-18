---
name: ckb-meta-strainphlan
description: >-
  Strain-level phylogenetic analysis using StrainPhlAn4. Takes per-sample marker
  consensus pickle files (.pkl) from ckb-meta-taxonomy (MetaPhlAn4), extracts
  markers for a target clade, and builds a RAxML phylogenetic tree. Input: a
  directory containing all sample .pkl files and a target species clade name.
  Use for strain-level microbiome diversity. Not for species-level profiling
  (use ckb-meta-taxonomy) or functional analysis.
compatibility: "MetaPhlAn4 ≥4.1 (includes StrainPhlAn4); RAxML ≥8; Python 3.10+; Linux x86_64; ≥64 GB RAM"
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

# ckb-meta-strainphlan：菌株水平系统发育分析

## Use When
- 需要对特定目标菌种进行菌株水平系统发育分析
- 已有所有样本的 MetaPhlAn4 .pkl 文件（来自 ckb-meta-taxonomy）
- 目标菌种在多个样本中均有足够 marker 覆盖

## Do Not Use When
| 需求 | 交给 |
|---|---|
| 物种组成 profile | ckb-meta-taxonomy |
| 功能注释 | ckb-meta-humann |
| 目标菌种丰度 <0.1% 的样本 | 不适用，marker 覆盖不足 |

## 软件依赖

```bash
# StrainPhlAn4 随 MetaPhlAn4 安装
which strainphlan && strainphlan --version
which extract_markers.py  # MetaPhlAn4 内置工具
which sample2markers.py   # MetaPhlAn4 内置工具
# 要求：MetaPhlAn >= 4.1.0
# 安装：conda install -c biobakery metaphlan=4.1.0

# RAxML（建树）
which raxmlHPC || which raxml
# 要求：RAxML >= 8.2
# 安装：conda install -c bioconda raxml=8.2.12
```

## 数据库依赖

| 数据库 | 版本 | 大小 | DCS 路径 | 说明 |
|---|---|---|---|---|
| MetaPhlAn4 SGB .pkl | mpa_vOct22_CHOCOPhlAnSGB_202212 | ~71 MB（.pkl 单文件）| `/public/database/CKB_metagenome/metaphlan/mpa_vOct22_CHOCOPhlAnSGB_202212.pkl` | 与 ckb-meta-taxonomy 共用 |

## Required Inputs

| 参数 | 说明 |
|---|---|
| pkls_dir | 所有样本 .pkl 文件所在**目录**（不是 glob 通配符，是目录路径）|
| clade | 目标菌种 clade 名称，格式如 `s__Phocaeicola_vulgatus` 或 SGB ID |
| dbs | MetaPhlAn4 数据库 .pkl 文件路径 |

## Necessary Questions

1. 用户未指定 clade → 询问目标菌种；可先看 ckb-meta-taxonomy profile 的高丰度物种
2. pkl 目录为空或样本数 <4 → 提示样本数不足，建树结果不可靠

## Workflow

**Gather**：确认 pkls_dir 下有 N 个 .pkl 文件，clade 存在于 MetaPhlAn4 数据库中

**Act**：
```bash
# Step 1: 提取目标 clade 的 marker
extract_markers.py \
  -d {dbs} \
  -c {clade} \
  -o ./{clade}/

# Step 2: StrainPhlAn4 建树
strainphlan \
  -d {dbs} \
  -s {pkls_dir}/*.pkl \
  -m ./{clade}/{clade}.fna \
  -o ./{clade}/result/ \
  -n 16 \
  -c {clade} \
  --mutation_rates \
  --marker_in_n_samples_perc 50 \
  --sample_with_n_markers 20 \
  --sample_with_n_markers_after_filt 20
```

**关键注意**：pkls_dir 必须传**目录路径**（如 `/work/.../strainphlan_pkls`），StrainPhlAn4 内部会 `./in/*.pkl` 收集所有文件。不要传通配符路径。

**DCS 平台**：投递 `strainphlan4_skill`，`Pkls` 参数传目录路径

**Verify**：`ls {clade}/result/RAxML_bestTree.*.tre`

## Output Contract

| 文件 | 说明 |
|---|---|
| `RAxML_bestTree.{clade}.StrainPhlAn4.tre` | 最优系统发育树（Newick 格式）|
| `RAxML_result.{clade}.StrainPhlAn4.tre` | RAxML 结果树 |
| `RAxML_info.{clade}.StrainPhlAn4.tre` | 模型摘要 |

## Guardrails

- Pkls 参数必须是目录，不是通配符（历史踩坑：`*.pkl` 会导致任务卡死）
- 样本数 <4 时 RAxML 建树无意义，停止并说明
- 目标菌丰度过低（<0.1%）的样本会被自动过滤，若全部样本均低丰度则失败

## Errors and Fallback

| 错误 | 处理 |
|---|---|
| `No markers found for clade` | 检查 clade 名称格式，或该菌在数据库中不存在 |
| 所有样本被过滤 | 降低 `--marker_in_n_samples_perc`（如 25），或检查目标菌丰度 |
| RAxML 建树失败（样本数不足）| 需至少 4 个有效样本 |

## Citation

- StrainPhlAn4: Costea et al., Nat Methods 2017; Blanco-Míguez et al., Nat Methods 2023
- RAxML: Stamatakis, Bioinformatics 2014
