---
name: geo-sra
description: >-
  Query NCBI GEO, SRA, and BioProject as a single-cell / spatial dataset discovery
  entry point. Supports keyword search for GSE series, GSE/GSM metadata, BioProject
  lookup, SRA Run details, and GSE→BioProject→download path resolution. Use for
  finding scRNA-seq / spatial datasets, processed matrix FTP links, SRR accessions,
  or raw-data access notes (EGA/dbGaP). Not for CNGB STOmics/CDCP atlas catalog
  (use stomics-datasets), HESTA spatial maps (use hesta), CIMA immune atlas (use
  cima), or running clustering/cell annotation (use sc-ingest / scanpy-*).
compatibility: Python 3.10+, HTTPS, optional NCBI_API_KEY
metadata:
  author: cngbdb-skill-team
  version: "1.0.0"
  scope: domain
  depth: L1-L2
  domain: discovery
  capability_id: cngbdb.discovery.geo-sra.v1
  load_strategy: domain-on-demand
  status: beta
  quality: Q3
  databases: [geo, sra, bioproject]
---

# GEO / SRA / BioProject 检索

公开组学归档发现入口：找得到、对得上、给出下载路径；**不做** scanpy/Seurat 分析。

## Use When

- 找公开 **单细胞 / 空间** 相关 GEO Series（GSE）
- 查看 **GSE / GSM / PRJNA / SRR** 元数据与补充矩阵 FTP
- 解析 **GSE → BioProject → SRA 或 EGA/dbGaP** 下载路径

## Do Not Use When

| 需求 | 交给 |
|------|------|
| 本地聚类 / 注释 / DE | `scanpy-*` / `sc-ingest`（本 skill 只给下载路径） |
| HESTA 人胚胎空间表达 | `hesta` |
| CNGB STOmics/CDCP 图谱 catalog | `stomics-datasets` |
| ClinVar / gnomAD 变异 | `clinvar` / `gnomad` |
| 已标准化细胞图谱切片 | CELLxGENE / HCA（若已部署） |
| 变异致病性 / 人群 AF | `clinvar` / `gnomad` |
| 基因坐标 / Ensembl ID | `ensembl` / `refseq` |

## Domain recognition

| 维度 | 约定 |
|------|------|
| 数据源 | NCBI GEO / SRA / BioProject（公开） |
| 默认偏向 | 单细胞 / 空间相关检索词（`search`） |
| 默认物种 | `Homo sapiens`（可用 `--organism ""` 取消） |
| 登录号 | GSE / GSM / PRJNA… / SRR\|ERR\|DRR |

## Required inputs

| 任务 | 必填 |
|------|------|
| 关键词检索 | `search` 关键词 |
| Series / Sample | GSE… / GSM… |
| BioProject / Run | PRJNA… / SRR… |
| 链路解析 | `resolve` + 上述登录号之一 |

## Necessary questions

1. 用户只说「找单细胞数据」但无组织/疾病 → 补问关键词  
2. 要「原始 fastq」时 → 用 `resolve`，区分 GEO 矩阵 / 公开 SRA / EGA·dbGaP  
3. 用户要跑聚类 → 说明超出本 skill，只给下载路径  

## Workflow

1. **Gather**：确认关键词或登录号、物种是否非人  
2. **Act**：只运行 `./scripts/query.py`  
3. **Verify**：核对登录号；注明矩阵 vs 原始测序 vs 受控库；附 NCBI 链接  

## Commands

```bash
python ./scripts/query.py search "<关键词>"
python ./scripts/query.py gse <GSE>
python ./scripts/query.py gsm <GSM>
python ./scripts/query.py bioproject <PRJNA…>
python ./scripts/query.py srr <SRR…>
python ./scripts/query.py sra_search "<关键词>"
python ./scripts/query.py resolve <GSE|GSM|PRJNA|SRR>
```

示例：

```bash
python ./scripts/query.py search "liver"
python ./scripts/query.py gse GSE149614
python ./scripts/query.py resolve GSE149614
```

依赖：`pip install -r ../../requirements.txt`；可选 `export NCBI_API_KEY=...`（使用本 Skill `scripts/_lib/ncbi_http.py`）。

## Output contract

- 文本表格/键值：登录号、标题、样本数、FTP、关联 PRJNA/SRR/EGA  
- Provenance：NCBI GEO/SRA URL、查询时间  
- **禁止**：编造不存在的 GSE/SRR；无结果时说明可换关键词或去掉物种限制  

## Guardrails

1. **必须**调用内置脚本，不得手写 E-utilities 冒充查询  
2. 不做下载完整矩阵/fastq，只打印路径与 `prefetch` 提示  
3. EGA/dbGaP 仅给登录号，说明需按仓库政策申请  
4. 「Sample type = SRA」≠ 一定有公开 SRR  

## Errors and fallback

| 情况 | 处理 |
|------|------|
| search 无结果 | 换英文关键词、放宽 `--organism ""` |
| BioProject 下 SRA=0 | 回 GEO 看补充矩阵或 EGA/dbGaP |
| 限流 / 网络失败 | 重试；设置 `NCBI_API_KEY` |

## Examples

**用户**：有没有人肝细胞癌单细胞数据集？  

**Agent**：`search "hepatocellular carcinoma"` 或 `search "liver HCC"` → 再 `gse` / `resolve`

**用户**：GSE149614 原始数据怎么下？  

**Agent**：`resolve GSE149614` → 区分矩阵 FTP / SRR / 受控库

## Citation

- GEO: https://www.ncbi.nlm.nih.gov/geo/  
- SRA: https://www.ncbi.nlm.nih.gov/sra/  
- BioProject: https://www.ncbi.nlm.nih.gov/bioproject/  

详细字段与坑见 [reference.md](reference.md)。
