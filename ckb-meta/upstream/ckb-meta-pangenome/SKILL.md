---
name: ckb-meta-pangenome
description: >-
  Pangenome analysis of MAGs from the same species using Prokka (gene annotation)
  followed by Panaroo (pangenome graph construction). Input: multiple MAG FASTA
  files from the same species/taxon (from ckb-meta-gtdbtk output, same species).
  Use when you have multiple same-species MAGs and need core/accessory/pan gene
  analysis. Requires ≥2 same-species MAGs. Not for cross-species MAG sets
  (Panaroo requires same species), nor for read-based profiling.
compatibility: "Prokka ≥1.14; Panaroo ≥1.3; Python 3.10+; Linux x86_64; ≥32 GB RAM"
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

# ckb-meta-pangenome：泛基因组分析

## Use When
- 已有同一物种的多个 MAG（来自 ckb-meta-gtdbtk 分类，筛选同物种）
- 需要分析 core gene、accessory gene 和 pan gene 集合
- 至少 2 个（建议 ≥3 个）同物种 MAG

## Do Not Use When
| 需求 | 交给 |
|---|---|
| 跨物种 MAG（Panaroo 不支持）| 请按物种分组后分批运行 |
| read-based 物种组成 | ckb-meta-taxonomy |
| 单个 MAG 基因注释只为分类 | ckb-meta-gtdbtk |

## 软件依赖

```bash
# Prokka（基因注释）
which prokka && prokka --version
# 要求：Prokka >= 1.14.6
# 安装：conda install -c conda-forge -c bioconda prokka=1.14.6

# Panaroo（泛基因组）
which panaroo && panaroo --version
# 要求：Panaroo >= 1.3.4
# 安装：conda install -c conda-forge -c bioconda panaroo=1.3.4
```

无数据库依赖（Prokka 使用自带参考蛋白数据库）。

## Required Inputs

| 参数 | 说明 |
|---|---|
| mag_fasta_list | 同物种 MAG FASTA 文件列表（至少 2 个）|
| genus | Prokka 注释时指定的菌属名（可选，提高注释准确性）|
| output_dir | 输出目录 |

## Necessary Questions

1. MAG 是否来自同一物种？（GTDB 分类结果中是否为同一 s__ 层级）→ 跨物种不能运行
2. MAG 数量 <2 → 停止，说明泛基因组需要至少 2 个基因组

## Workflow

**Gather**：确认所有 MAG FASTA 路径，确认均为同物种

**Act**：
```bash
# Step 1: Prokka 注释每个 MAG
for mag in {mag_fasta_list}; do
  sample=$(basename $mag .fa)
  prokka --outdir prokka_${sample} \
    --prefix ${sample} \
    --metagenome \
    --cpus 8 \
    ${mag}
done

# Step 2: Panaroo 泛基因组
panaroo \
  -i prokka_*/*.gff \
  -o {output_dir}/panaroo_out \
  --clean-mode strict \
  -t 8 \
  2>{output_dir}/panaroo.log
```

**DCS 平台**：投递 `prokka_panaroo_skill`

**重要约束**：Panaroo 要求输入 GFF 来自**同一物种**的不同菌株。跨物种混合输入会导致 `core_gene_alignment` 为空或 numpy 数组边界错误。

**Verify**：`cat {output_dir}/panaroo_out/summary_statistics.txt`

## Output Contract

| 文件 | 说明 |
|---|---|
| `summary_statistics.txt` | core/soft-core/shell/cloud 基因统计 |
| `pan_genome_reference.fa` | pan-genome 参考序列 |
| `core_gene_alignment.aln` | core 基因多序列比对（可用于建树）|
| `gene_presence_absence.csv` | 每个基因在各 MAG 中的存在/缺失 |

## Guardrails

- 严格要求同物种输入；跨物种会导致 Panaroo 内部崩溃
- 数据量少（demo 数据）可能产生空 core gene；属正常现象，非 skill 缺陷
- `--clean-mode strict` 默认去除污染；基因组质量差时可尝试 `moderate`

## Errors and Fallback

| 错误 | 处理 |
|---|---|
| `No core genes found` | 确认输入 MAG 为同物种；或数量不足 |
| `np.quantile empty array` | Panaroo 内部 bug，见于跨物种或极少 MAG 情况；改用 `--clean-mode pan` |
| Prokka 注释报错 | 检查 MAG FASTA 是否有效（非空、非截断）|

## Citation

- Prokka: Seemann, Bioinformatics 2014. https://github.com/tseemann/prokka
- Panaroo: Tonkin-Hill et al., Genome Biol 2020. https://github.com/gtonkinhill/panaroo
