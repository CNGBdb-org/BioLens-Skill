---
name: ckb-meta-qc
description: >-
  Metagenomics QC and host removal for paired-end FASTQ. Runs fastp (adapter
  trimming, quality filtering, min-length) then Bowtie2 to remove human host
  reads using CHM13 v2.0 index. Outputs clean rmhost FASTQ for downstream
  assembly, taxonomy profiling, and functional annotation. Use for any
  metagenomics sample before assembly or profiling. Not for 16S amplicon,
  host-genome alignment, or single-end-only trimming (use ckb-meta-humann SE path).
compatibility: "fastp ≥0.23; bowtie2 ≥2.4; samtools ≥1.15; Python 3.10+; Linux x86_64"
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

# ckb-meta-qc：质控与去宿主

## Use When
- 原始双端宏基因组 FASTQ 需要质控和去人源宿主
- 下游需要进行组装（ckb-meta-assembly）或物种注释（ckb-meta-taxonomy）

## Do Not Use When
| 需求 | 交给 |
|---|---|
| 16S 扩增子质控 | 16S skills |
| 非人类宿主去除 | 本 skill 可用，但需替换 CHM13 索引为对应物种参考 |
| 已完成去宿主 | 直接进 ckb-meta-assembly 或 ckb-meta-taxonomy |

## 软件依赖（环境检测顺序）

Agent 运行前必须按顺序检测，缺失时停止并告知用户：

```bash
# 1. 检测 DCS 平台
dcs --version

# 2. 检测 fastp
which fastp && fastp --version
# 要求：fastp >= 0.23.4
# 安装：conda install -c bioconda fastp=0.23.4
#       或 https://github.com/OpenGene/fastp/releases

# 3. 检测 bowtie2
which bowtie2 && bowtie2 --version
# 要求：bowtie2 >= 2.4.5
# 安装：conda install -c bioconda bowtie2=2.4.5

# 4. 检测 samtools
which samtools && samtools --version
# 要求：samtools >= 1.15
# 安装：conda install -c bioconda samtools=1.15
```

## 数据库依赖

| 数据库 | 版本 | 大小 | DCS 路径 | 官方下载 |
|---|---|---|---|---|
| CHM13 Bowtie2 索引 | v2.0 (T2T) | ~4.1 GB | `/public/database/CKB_metagenome/CHM13/` | https://github.com/marbl/CHM13 → bowtie2 index |

非 DCS 环境自行下载后，设置环境变量：
```bash
export CKB_HOST_REF=/path/to/CHM13_bowtie2_index/CHM13
```

## Required Inputs

| 参数 | 说明 |
|---|---|
| input_fq1 | R1 原始 FASTQ（.fq.gz） |
| input_fq2 | R2 原始 FASTQ（.fq.gz） |
| sampleid | 样本 ID（输出文件前缀） |
| host_ref | Bowtie2 索引前缀路径（默认 CHM13） |

## Necessary Questions

1. 用户未提供 R1/R2 路径 → 询问 FASTQ 路径
2. 非人类样本 → 询问宿主物种，提示需要替换参考索引

## Workflow

**Gather**：确认输入 FASTQ 路径、样本 ID、宿主参考路径

**Act**：
```bash
# Step 1: fastp 质控
fastp \
  -i {input_fq1} -I {input_fq2} \
  -o {sampleid}.trim.1.fq.gz -O {sampleid}.trim.2.fq.gz \
  --adapter_sequence AAGTCGGAGGCCAAGCGGTCTTAGGAAGACAA \
  --adapter_sequence_r2 AAGTCGGATCGTAGCCATGTCGTTCTGTGAGCCAAGGAGTTG \
  --length_required 30 \
  --thread 4 \
  -j {sampleid}.fastp.json -h {sampleid}.fastp.html \
  2>{sampleid}.fastp.log

# Step 2: Bowtie2 去宿主
bowtie2 -x {host_ref} \
  -1 {sampleid}.trim.1.fq.gz -2 {sampleid}.trim.2.fq.gz \
  --threads 4 --un-conc-gz {sampleid}.rmhost_CHM13.%.fq.gz \
  -S /dev/null \
  2>{sampleid}.rmhost_CHM13.log
```

**DCS 平台**：投递 `qc_skill`，参数见 `references/dcs_params.md`

**Verify**：检查 `{sampleid}.rmhost_CHM13.1.fq.gz` 非空；查看 fastp.json 中 `summary.after_filtering.total_reads`

## Output Contract

| 文件 | 说明 |
|---|---|
| `{sampleid}.rmhost_CHM13.1.fq.gz` | 去宿主后 R1，传入 ckb-meta-assembly / ckb-meta-taxonomy / ckb-meta-humann |
| `{sampleid}.rmhost_CHM13.2.fq.gz` | 去宿主后 R2 |
| `{sampleid}.fastp.json` | QC 统计 |
| `{sampleid}.fastp.html` | QC 报告 |
| `{sampleid}.rmhost_CHM13.log` | Bowtie2 比对日志（记录去除宿主 reads 比例） |

## Guardrails

- 不跳过去宿主步骤直接进行组装或注释
- 未检测到 fastp / bowtie2 时，列出安装命令后停止，不自行安装
- 不修改原始 FASTQ

## Errors and Fallback

| 错误 | 处理 |
|---|---|
| fastp 报 out of memory | 减少 `--thread`，或增大系统内存 |
| bowtie2 找不到索引 | 检查 host_ref 路径是否含 .1.bt2 / .1.bt2l 文件 |
| 输出 rmhost 文件为空 | 检查接头序列是否匹配，或样本本身 reads 极少 |

## Citation

- fastp: Chen et al., Bioinformatics 2018. https://github.com/OpenGene/fastp
- Bowtie2: Langmead & Salzberg, Nat Methods 2012
- CHM13 T2T: Nurk et al., Science 2022. https://github.com/marbl/CHM13
