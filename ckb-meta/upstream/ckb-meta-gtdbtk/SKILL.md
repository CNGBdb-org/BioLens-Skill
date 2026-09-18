---
name: ckb-meta-gtdbtk
description: >-
  Taxonomic classification of MAGs using GTDB-Tk r226. Takes quality-filtered
  MAG bins from ckb-meta-checkm2, assigns taxonomy against GTDB release 226
  database. Use for assembly-based MAG taxonomy after quality assessment.
  Not for read-based profiling (use ckb-meta-taxonomy). Requires ≥200 GB RAM and
  ~132 GB database; plan resources accordingly.
compatibility: "GTDB-Tk ≥2.3; Python 3.10+; Linux x86_64; ≥200 GB RAM; ≥132 GB disk for database"
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

# ckb-meta-gtdbtk：GTDB-Tk MAG 物种分类

## Use When
- 需要对 MAG bins 做参考数据库级物种分类（GTDB taxonomy）
- 输入来自 ckb-meta-checkm2 过滤后的高质量 MAG

## Do Not Use When
| 需求 | 交给 |
|---|---|
| Read-based 物种 profile | ckb-meta-taxonomy |
| 未经质控的 bins | 先做 ckb-meta-checkm2 |

## 软件依赖

```bash
which gtdbtk && gtdbtk --version
# 要求：GTDB-Tk >= 2.3.2
# 安装：conda install -c conda-forge -c bioconda gtdbtk=2.3.2
#       注意：需要单独下载数据库（见下方）
```

## 数据库依赖

| 数据库 | 版本 | 大小 | DCS 路径 | 官方下载 |
|---|---|---|---|---|
| GTDB-Tk 参考数据库 | Release 226 (r226) | ~132 GB | `/public/database/CKB_metagenome/gtdbtk/gtdbtk_r226_data.tar.gz` | https://data.gtdb.ecogenomic.org/releases/release226/ |

非 DCS 环境：
```bash
# 下载（约 132 GB，建议用 wget 续传）
wget https://data.gtdb.ecogenomic.org/releases/release226/auxillary_files/gtdbtk_package/full_package/gtdbtk_r226_data.tar.gz

# 解压
tar -xzf gtdbtk_r226_data.tar.gz -C /path/to/gtdbtk_db/

# 配置环境变量
export GTDBTK_DATA_PATH=/path/to/gtdbtk_db/release226
# 或修改 conda 环境中的 gtdbtk.sh 配置文件
```

## Required Inputs

| 参数 | 说明 |
|---|---|
| bins_dir | 高质量 MAG bins 目录（.fa 文件，来自 ckb-meta-checkm2 过滤后）|
| sampleid | 样本 ID |
| db_path | GTDB-Tk release226 数据库目录路径 |

## Workflow

**Gather**：确认 bins 目录、数据库路径（需含 release226/ 子目录结构）

**Act**：
```bash
# MAG bins 目录需解压（DCS 输出为 tar.gz）
tar -xzf {semibin_tarball} -C {bins_dir}/
gunzip {bins_dir}/*.fa.gz 2>/dev/null || true

# GTDB-Tk classify
gtdbtk classify_wf \
  --genome_dir {bins_dir} \
  --out_dir {sampleid}_gtdbtk_out \
  --cpus 16 \
  --skip_ani_screen \
  -x fa \
  2>{sampleid}.gtdbtk.log
```

**DCS 平台**：投递 `gtdbtk_skill_noway`（输入 semibin2.tar.gz，WDL 内部自动解压）

**Verify**：`cat {sampleid}_gtdbtk_out/gtdbtk.bac120.summary.tsv | wc -l`

## Output Contract

| 文件 | 说明 |
|---|---|
| `gtdbtk.bac120.summary.tsv` | 细菌 MAG 分类结果（GTDB 分类路径）|
| `gtdbtk.ar53.summary.tsv` | 古菌 MAG 分类结果 |

## Guardrails

- 内存要求高（≥200 GB），环境不满足时停止并说明资源需求
- 不在低质量 MAG（completeness <50%）上运行

## Errors and Fallback

| 错误 | 处理 |
|---|---|
| GTDBTK_DATA_PATH 未设置 | 提示设置环境变量或指定 --gtdbtk_data_path |
| pplacer OOM | 需要更大内存节点（≥256 GB）|

## Citation

- GTDB-Tk: Parks et al., Nat Biotechnol 2022. https://github.com/Ecogenomics/GTDBTk
- GTDB r226: https://gtdb.ecogenomic.org/
