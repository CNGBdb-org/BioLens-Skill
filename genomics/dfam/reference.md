# Dfam 查询 — 解读路径

## 研究者典型工作流

| 工作流 | 推荐命令 | 目的 |
|--------|----------|------|
| 重复家族注释 | `family` | 名称/accession → 家族元数据 |
| 家族发现 | `search` | 关键词浏览 Dfam 库 |
| HMM 参数 | `model` | 建模长度与阈值 |
| 类型分类 | `repeat` | LINE/SINE/LTR 等 |
| 基因组坐标 | `region` + **ucsc** | Dfam 无区间 API → RepeatMasker |

## 输入 → 输出

### 按家族（family）

```
名称（Alu）或 accession（DF0000001）
  → GET dfam.org/api/families?name={name}
  → 无结果 → ?accession={name}
  → accession, name, title, description, repeat_type, species
```

### 搜索（search）

```
关键词（MER, Alu）
  → GET /families?name={keyword}&limit=N
  → total_count + 结果列表
```

### 模型（model）

```
accession（DF0000001）
  → GET /families/{acc} 或列表回退
  → length, gathering_threshold, repeat_type
```

### 重复类型（repeat）

```
类型（LINE, SINE, LTR）
  → GET /families?repeat_type={keyword}
  → 无结果则按 name 回退搜索
```

### 区域（region）— 无直接 API

```
chr1:1000000-1010000
  → 脚本输出说明 + UCSC 联动命令
  → ucsc track RepeatMasker <region>
  → dfam family <元件名> 查家族详情
```

## 核心字段

| 字段 | 说明 |
|------|------|
| accession | Dfam 家族编号（DF…） |
| name | 家族短名（如 AluJb） |
| repeat_type | LINE、SINE、LTR、DNA 等 |
| gathering_threshold | HMM 可靠检测阈值 |
| length | 共识序列长度 |

## 注意点

- Dfam 公共 API 面向**家族元数据**，不含基因组坐标注释
- 坐标级重复注释依赖 **RepeatMasker**（UCSC track 或本地运行）
- 区域工作流：`dfam region`（说明）→ `ucsc track RepeatMasker` → `dfam family`
- 描述字段可能较长，脚本截断展示前 200 字符

## API 参考

- [Dfam API](https://dfam.org/api)
- [Dfam](https://dfam.org/)
- 区域注释：[UCSC RepeatMasker](https://genome.ucsc.edu/)（见 `ucsc` skill）
