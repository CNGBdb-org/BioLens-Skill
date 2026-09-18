---
name: ckb-meta-binning
description: >-
  Metagenome-assembled genome (MAG) binning. Aligns clean reads back to contigs
  with Bowtie2, sorts BAM with samtools, then bins with SemiBin2 (global model).
  Input: contigs.fa from ckb-meta-assembly + rmhost FASTQ from ckb-meta-qc.
  Output: per-sample MAG bins for quality assessment (ckb-meta-checkm2) and
  taxonomy (ckb-meta-gtdbtk). Not for read-based profiling (use ckb-meta-taxonomy).
compatibility: "bowtie2 ≥2.4.5; samtools ≥1.15; SemiBin2 ≥2.0; Python 3.10+; Linux x86_64; ≥64 GB RAM recommended"
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

# ckb-meta-binning：MAG 分箱

## Use When
- 需要从组装 contigs 重建 MAG（Metagenome-Assembled Genomes）
- 已有 ckb-meta-assembly 的 contigs.fa 和 ckb-meta-qc 的 rmhost FASTQ

## Do Not Use When
| 需求 | 交给 |
|---|---|
| read-based 物种注释 | ckb-meta-taxonomy |
| 无需 MAG，只做功能注释 | ckb-meta-humann |

## 软件依赖

```bash
# bowtie2（reads 回贴）
which bowtie2 && bowtie2 --version
# 要求：>= 2.4.5，安装：conda install -c bioconda bowtie2=2.4.5

# samtools（BAM 排序）
which samtools && samtools --version
# 要求：>= 1.15，安装：conda install -c bioconda samtools=1.15

# SemiBin2（分箱）
which SemiBin && SemiBin --version
# 要求：SemiBin2 >= 2.0
# 安装：conda install -c bioconda semibin=2.0
#       或 pip install SemiBin
```

无数据库依赖（使用 global 内置模型）。

## Required Inputs

| 参数 | 说明 |
|---|---|
| contigs_fa | ckb-meta-assembly 输出的 {sampleid}.contigs.fa |
| cleaned_reads_fq1 | rmhost R1（ckb-meta-qc 输出） |
| cleaned_reads_fq2 | rmhost R2（ckb-meta-qc 输出） |
| sampleid | 样本 ID |

## Workflow

**Gather**：确认 contigs.fa / R1 / R2 路径

**Act**：
```bash
# Step 1: 建 bowtie2 索引
bowtie2-build {contigs_fa} {sampleid}_contigs_index

# Step 2: reads 回贴
bowtie2 -x {sampleid}_contigs_index \
  -1 {cleaned_reads_fq1} -2 {cleaned_reads_fq2} \
  -p 8 --no-unal | \
  samtools sort -@ 8 -o {sampleid}.sorted.bam && \
  samtools index {sampleid}.sorted.bam

# Step 3: SemiBin2 分箱
SemiBin2 single_easy_bin \
  -i {contigs_fa} \
  -b {sampleid}.sorted.bam \
  -o {sampleid}_semibin2 \
  --environment global \
  -t 4
```

**DCS 平台**：投递 `bowtie_Semibin2_skill`

**Verify**：`ls {sampleid}_semibin2/output_bins/ | wc -l` 应 >0

## Output Contract

| 文件/目录 | 说明 | 下游 |
|---|---|---|
| `{sampleid}_semibin2/output_bins/*.fa` | MAG bins | ckb-meta-checkm2, ckb-meta-gtdbtk, ckb-meta-pangenome |
| `{sampleid}.sorted.bam` | 排序后 BAM | - |

## Guardrails

- reads 数量 <500 万时分箱结果可能为空，提示用户数据量不足
- 不使用 `-environment` 以外的自训练模型（需要更多数据和时间）

## Errors and Fallback

| 错误 | 处理 |
|---|---|
| bins 数为 0 | 检查 contigs 数量和 reads 深度；数据量过少属于预期 |
| samtools sort OOM | 减少 `-@` 线程，或加大内存 |

## Citation

- SemiBin2: Pan et al., Nat Commun 2023. https://github.com/BigDataBiology/SemiBin
- Bowtie2: Langmead & Salzberg, Nat Methods 2012
