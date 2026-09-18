---
name: ckb-meta-assembly
description: >-
  De novo metagenome assembly from paired-end clean reads using MEGAHIT.
  Takes rmhost FASTQ from ckb-meta-qc, produces contigs.fa for downstream
  binning (ckb-meta-binning). Use for metagenome assembly step. Not for
  read-based taxonomy profiling (use ckb-meta-taxonomy) or reference-based
  alignment.
compatibility: "MEGAHIT ≥1.2.9; Python 3.10+; Linux x86_64; ≥32 GB RAM recommended"
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

# ckb-meta-assembly：宏基因组组装

## Use When
- 需要从 clean reads 组装 contigs，用于后续 MAG 分箱
- 输入来自 ckb-meta-qc 的 rmhost FASTQ

## Do Not Use When
| 需求 | 交给 |
|---|---|
| 物种组成 profile（不需要组装） | ckb-meta-taxonomy |
| 功能注释（read-based）| ckb-meta-humann |
| 已有 contigs | 直接进 ckb-meta-binning |

## 软件依赖

```bash
which megahit && megahit --version
# 要求：MEGAHIT >= 1.2.9
# 安装：conda install -c bioconda megahit=1.2.9
#       或 https://github.com/voutcn/megahit/releases
```

无数据库依赖。

## Required Inputs

| 参数 | 说明 |
|---|---|
| cleaned_reads_fq1 | rmhost R1（来自 ckb-meta-qc） |
| cleaned_reads_fq2 | rmhost R2（来自 ckb-meta-qc） |
| sampleid | 样本 ID |

## Workflow

**Gather**：确认 R1/R2 路径，检查文件非空

**Act**：
```bash
megahit \
  -1 {cleaned_reads_fq1} -2 {cleaned_reads_fq2} \
  --k-list 21,33,55,77 \
  --min-contig-len 100 \
  -t 12 \
  -o {sampleid}.megahit.out \
  2>{sampleid}.megahit.log

cp {sampleid}.megahit.out/final.contigs.fa {sampleid}.contigs.fa
```

**DCS 平台**：投递 `Megahit_skill`

**Verify**：`grep -c ">" {sampleid}.contigs.fa` 应 >0

## Output Contract

| 文件 | 说明 | 下游 |
|---|---|---|
| `{sampleid}.contigs.fa` | 组装 contigs | ckb-meta-binning |
| `{sampleid}.megahit.log` | 运行日志 | - |

## Guardrails

- 内存不足（<32GB）时提示用户，不强行运行
- min-contig-len 默认 100 bp，不低于此值

## Errors and Fallback

| 错误 | 处理 |
|---|---|
| out of memory | 减少 `-t` 线程数，或加大 swap |
| 输出 contigs 为空 | 检查输入 reads 数量是否过少（<100万 reads 可能组装失败）|

## Citation

- MEGAHIT: Li et al., Bioinformatics 2015. https://github.com/voutcn/megahit
