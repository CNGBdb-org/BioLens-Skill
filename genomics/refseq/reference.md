# RefSeq 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 基因 ID | `gene` | RefSeq Gene → 坐标与描述 |
| 转录本验证 | `transcript` | NM_ accession 详情 |
| 蛋白验证 | `protein` | NP_ accession 详情 |
| 区域注释 | `region` | 区间内 RefSeq 基因 |

## 输入 → 输出

### 按基因（gene）

```
基因符号
  → esearch gene: {symbol}[gene] AND homo sapiens[orgn]
  → esummary → uid、name、description、chromosome、genomicinfo
```

### 按转录本（transcript）

```
NM_007294
  → esearch nuccore: {accession}
  → esummary → title、slen、updatedate
```

### 按蛋白（protein）

```
NP_009225
  → esearch protein: {accession}
  → esummary → title、slen
```

### 按区域（region）

```
chr17:43044295-43170245
  → 解析为 17[43044295:43170245][Gene]
  → esearch gene → esummary
```

## 核心字段

| 字段 | 说明 |
|------|------|
| uid | NCBI Gene ID（Entrez） |
| accessionversion | RefSeq accession（转录本/蛋白） |
| genomicinfo | chrstart、chrstop 坐标 |
| slen | 序列长度 |

## 注意点

- RefSeq 与 Ensembl 转录本可能不完全一致，对比时用 `ensembl gene`
- E-utilities 限流：避免短时间内大量请求
- 临床变异注释常需 RefSeq 转录本 + HGVS，可联动 `ensembl vep`

## API 参考

- [NCBI E-utilities](https://www.ncbi.nlm.nih.gov/home/develop/api/)
- [RefSeq](https://www.ncbi.nlm.nih.gov/refseq/)
