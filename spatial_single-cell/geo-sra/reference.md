# GEO / SRA / BioProject — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 课题冷启动找数据 | `search` | 快速列出相关 GSE |
| 判断能否直接分析 | `gse` / `resolve` | 看有无 count/h5/mtx 等补充文件 |
| 样本表型 / 分组 | `gsm` | tissue、patient、treatment 等 characteristics |
| 项目级汇总 | `bioproject` | 一篇论文对应的测序项目 |
| 已知 Run 下载 | `srr` | runinfo + prefetch 指引 |
| 登录号互查 | `resolve` | GSE↔BioProject↔SRA/EGA |

## 输入 → 输出

### search

```
关键词（liver, PBMC COVID, spatial breast）
  → GDS esearch：关键词 AND 单细胞/空间提示词 AND GSE[Entry Type] AND 物种
  → esummary → 登录号、标题、样本数、FTP
```

### gse

```
GSE…
  → GEO SOFT text（acc.cgi form=text）
  → 标题/摘要/设计/样本列表/Series_relation/补充文件
  → 抽取 BioProject、EGA、dbGaP、SRP/SRR（若有）
```

### gsm

```
GSM…
  → GEO SOFT full
  → characteristics、文库、Series、BioSample
  → 尝试 BioSample elink → SRA runinfo（常失败：数据在受控库）
```

### bioproject / srr

```
PRJNA… → bioproject esummary + elink GEO/SRA
SRR…   → sra esearch + efetch rettype=runinfo
```

### resolve

```
GSE…
  → soft 元数据
  → 统计补充矩阵文件
  → 展开 BioProject / 提示 EGA/dbGaP
  → 给出「下矩阵 / 拉 fastq / 申请受控库」三选一建议
```

## 字段速查

| 字段 | 含义 |
|------|------|
| GSE | GEO Series（一项研究） |
| GSM | GEO Sample（一个文库/样本） |
| GPL | 平台（如 10x 相关平台） |
| PRJNA/PRJEB… | BioProject |
| SRR/SRX/SRP | SRA Run / Experiment / Study |
| 补充文件 | GEO 上的矩阵、注释表等（常可直接分析） |
| EGA / dbGaP | 受控访问原始数据 |

## 常见坑

| 现象 | 解释 |
|------|------|
| Sample type = SRA 但无 SRR | 仅表示测序型样本；原始数据可能未公开到 SRA |
| `bioproject` 下 SRA 命中 0 | 原始数据在 EGA/dbGaP，或仅上传了处理后矩阵 |
| search 结果偏新/偏多 | 单细胞词会放大召回；请再 `gse` 人工筛选 |
| FTP 路径 | 脚本按 NCBI 惯例 `{GSExxx}nnn` 拼接；以页面/补充文件链接为准 |

## 不做的事

- 不下载完整 fastq/矩阵到本地（只打印路径与命令提示）
- 不运行 QC、聚类、cell type 注释、差异表达
- 不替代 CELLxGENE 等已标准化细胞图谱查询
