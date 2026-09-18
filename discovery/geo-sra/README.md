# GEO / SRA / BioProject

NCBI **GEO**（表达归档）、**SRA**（原始测序）与 **BioProject**（项目汇总）公开组学发现入口。用于找 **单细胞/空间** 相关数据集并给出下载路径，**不运行**聚类、注释或差异分析。

## 能查什么

| 类型 | 说明 |
|------|------|
| 关键词检索 | 找相关 GSE（默认偏向 single-cell / spatial / 10x） |
| Series / Sample | GSE / GSM 元数据与补充矩阵 FTP |
| BioProject / Run | PRJNA…、SRR runinfo 与 prefetch 指引 |
| 链路解析 | GSE → 矩阵 / BioProject / SRA / EGA / dbGaP |

## 运行

```bash
cd skills/discovery/geo-sra
python ./scripts/query.py search "liver"
python ./scripts/query.py gse GSE149614
python ./scripts/query.py resolve GSE149614
```

依赖：`pip install -r ../../requirements.txt`；可选 `NCBI_API_KEY`。

## 示例问法

- 有没有人肝脏单细胞 RNA-seq 数据？
- GSE149614 是什么数据？有没有表达矩阵？
- GSE149614 原始 fastq 怎么下？

## 边界

- 许多 GSM「Sample type = SRA」并不意味着 fastq 一定公开在 SRA。  
- EGA / dbGaP 仅给登录号，需按政策申请。  
- HESTA 空间表达请用 `hesta`。
