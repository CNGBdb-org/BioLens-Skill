# UCSC 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 基因定位 | `gene` | UCSC 搜索基因坐标 |
| 区域注释 | `region` | knownGene 基因列表 |
| 自定义 track | `track` | RepeatMasker、refGene 等 |
| 进化保守 | `conservation` | phastCons 可用性探测 |

## 输入 → 输出

### 按 track（track）

```
track名 + 区域（RepeatMasker chr1:1-100000）
  → GET api.genome.ucsc.edu/getData/track
     ?genome={genome}&track={track}&chrom&start&end
  → 解析 JSON 中 track 对应数组
```

### 按基因（gene）

```
基因符号（BRCA1）
  → GET api.genome.ucsc.edu/search?genome={genome}&query={symbol}
  → 匹配基因名与坐标
```

### 按区域（region）

```
区域坐标
  → 等价 track knownGene <region>
```

### 保守性（conservation）

```
区域坐标
  → 依次尝试 phastCons100way、phastCons30way
  → 有数据则报告；否则提示 bigWig / Ensembl
```

## 常用 track

| Track | 用途 |
|-------|------|
| knownGene | UCSC 已知基因 |
| refGene | RefSeq 基因 |
| RepeatMasker | 重复元件注释（联动 dfam） |
| phastCons100way | 100 物种保守性 |

## 核心字段

| 字段 | 说明 |
|------|------|
| name / geneName | 基因或元件名 |
| chromStart / txStart | 区间起点 |
| chromEnd / txEnd | 区间终点 |
| genome | 组装版本（默认 hg38） |

## 注意点

- track 名称须与 UCSC 浏览器一致（大小写敏感）
- API 返回结构因 track 而异，脚本自动探测数据键
- 保守性 API 可能无逐碱基分数，精细分析用 bigWig 下载
- hg19 等旧组装需 `--genome hg19`

## API 参考

- [UCSC Genome Browser API](https://api.genome.ucsc.edu/)
- [UCSC Genome Browser](https://genome.ucsc.edu/)
