---
name: ckb-meta-merge
description: >-
  Multi-sample merge layer for CKB metagenomics pipeline. Merges per-sample
  MetaPhlAn4 species profiles into a multi-sample abundance matrix using
  merge_metaphlan_tables.py; merges per-sample HUMAnN3 functional tables using
  humann_join_tables. Also validates merged matrix against metadata sample ID
  consistency. Must be run after all upstream samples complete and before any
  downstream statistical analysis. Not for single-sample analysis or raw FASTQ
  processing (use upstream skills).
compatibility: "MetaPhlAn4 ≥4.1 (merge_metaphlan_tables.py); HUMAnN3 ≥3.9 (humann_join_tables); Python 3.10+"
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

# ckb-meta-merge：多样本矩阵合并

## Use When
- 所有样本已完成 ckb-meta-taxonomy（物种 profile）或 ckb-meta-humann（功能注释）
- 需要生成多样本合并矩阵，进入下游统计分析
- 需要验证矩阵与 metadata 的样本 ID 一致性

## Do Not Use When
| 需求 | 交给 |
|---|---|
| 单样本分析 | upstream skills 直接用 |
| 已有 merged 矩阵 | 直接进对应 downstream skill |
| MAG 去冗余 | 使用 drep（可选，DCS: drep_skill_noway）|

## 软件依赖

```bash
# merge_metaphlan_tables.py（随 MetaPhlAn4 安装）
which merge_metaphlan_tables.py
# 要求：MetaPhlAn >= 4.1.0
# 安装：conda install -c biobakery metaphlan=4.1.0

# humann_join_tables（随 HUMAnN3 安装）
which humann_join_tables
# 要求：HUMAnN >= 3.9
# 安装：conda create -n biobakery3 -c biobakery humann=3.9
```

## Required Inputs

### 场景一：MetaPhlAn4 物种 profile 合并

| 参数 | 说明 |
|---|---|
| profile_dir | 含所有样本 .mp4.profile 文件的目录 |
| output_path | 合并矩阵输出路径（建议 merged_species_abundance.tsv）|

### 场景二：HUMAnN3 功能注释合并

| 参数 | 说明 |
|---|---|
| humann_output_dir | 含各样本 humann3 输出目录或解压后文件的目录 |
| file_type | `pathabundance` / `genefamilies` / `pathcoverage` |
| output_path | 合并矩阵输出路径 |

## Workflow

**Gather**：确认 N 个样本的 per-sample 文件均存在

**Act（物种 profile）**：
```bash
# 合并所有样本 profile
merge_metaphlan_tables.py {profile_dir}/*.mp4.profile \
  > merged_species_abundance.tsv

# 过滤到 species 层（必须步骤）
grep -E "(^#|s__)" merged_species_abundance.tsv | grep -v "t__" \
  > merged_species_only.tsv

# 验证
python3 scripts/check_merge_quality.py \
  --matrix merged_species_only.tsv \
  --metadata metadata.tsv \
  --sample-id-col sample_id
```

**Act（功能注释）**：
```bash
# pathabundance 合并
humann_join_tables \
  --input {humann_output_dir} \
  --file_name pathabundance \
  --output merged_pathabundance.tsv

# genefamilies 合并
humann_join_tables \
  --input {humann_output_dir} \
  --file_name genefamilies \
  --output merged_genefamilies.tsv
```

**Verify**：
- 矩阵列数 = 样本数（加 1，第一列为 feature 名）
- 矩阵行数 >10（物种数或功能数合理）
- metadata 样本 ID 与矩阵列名完全对应

## Output Contract

| 文件 | 说明 | 下游 |
|---|---|---|
| `merged_species_only.tsv` | 多样本物种丰度矩阵（s__ 层级）| community/differential/association/ML/survival |
| `merged_pathabundance.tsv` | 多样本通路丰度矩阵 | functional-analysis |
| `merged_genefamilies.tsv` | 多样本基因家族矩阵 | functional-analysis |
| `metadata.tsv` | 样本元数据（含 group/label/time/status 等）| 所有 downstream |

## 质检规则（每次 merge 后必须执行）

1. 矩阵行数（feature 数）是否合理（物种矩阵通常 50~500 行）
2. 矩阵列数（样本数）是否与预期一致
3. 是否存在大量 NaN / 全零列（某样本全为 0 → 检查该样本上游结果）
4. metadata 样本 ID 与矩阵列名是否一一对应（不对应则停止，不强行进入下游）

## Guardrails

- 进入 downstream 之前必须经过 merge，禁止直接用 per-sample 文件跑下游统计
- 物种矩阵必须过滤到 s__ 层（去掉 t__ 株水平条目）再进入 downstream

## Errors and Fallback

| 错误 | 处理 |
|---|---|
| profile 格式不一致 | 检查各样本 profile 文件头部，确认都是 MetaPhlAn4 v4 格式 |
| humann_join_tables 找不到文件 | 确认 humann_output_dir 下各样本目录已解压 |
| metadata 样本 ID 不匹配 | 停止，列出不匹配的样本名，要求用户核对 |

## Citation

- MetaPhlAn4: Blanco-Míguez et al., Nat Methods 2023
- HUMAnN3: Franzosa et al., Nat Methods 2018
