# Spatial / Single-cell Skills

面向公开单细胞与空间转录组分析的 Agent Skills 集合，收录于 [BioLens-Skill](https://github.com/CNGBdb-org/BioLens-Skill)。本目录包含 **13** 个可独立安装的叶子 Skill，覆盖 GEO/SRA 数据发现、scRNA 摄取与 Scanpy 流水线，以及空间转录组摄取 / QC / SVG / 解卷积 / 邻域互作。

技术栈以 Scanpy / AnnData 为主；空间相关步骤在有 Squidpy 时优先使用，否则走内置回退实现。本包为通用本地分析能力，**不包含** HESTA / MOSTA / STOmics 等图谱门户 Skill。

```text
spatial_single-cell/
├── install-to-agent.sh   # 安装至各类 Agent
├── requirements.txt      # Python 依赖
├── README.md
├── geo-sra/
├── sc-ingest/
├── scanpy-qc/
├── spatial-ingest/
└── …
```

安装完成后，Agent 侧目录形态为：`<skills-dir>/<skill-name>/SKILL.md`。

---

## 安装

### Python 依赖

```bash
git clone https://github.com/CNGBdb-org/BioLens-Skill.git
cd BioLens-Skill/spatial_single-cell
python -m pip install -r requirements.txt
```

该依赖清单覆盖 GEO/SRA 检索与 Scanpy 单细胞 / 空间基线流程。可选组件（`scvi-tools`、`squidpy`、`spatialdata`）见 `requirements.txt` 末尾注释；各 Skill 的兼容性说明亦见对应 `SKILL.md`。

### Agent 目标路径

| Agent | 项目级 | 用户级（全局） |
|-------|--------|----------------|
| Cursor | `.cursor/skills/` | `~/.cursor/skills/` |
| Claude Code | `.claude/skills/` | `~/.claude/skills/` |
| Codex | `.agents/skills/` | `~/.codex/skills/` |
| Gemini CLI | `.agents/skills/` | `~/.gemini/skills/` |
| Antigravity | `.agents/skills/` | `~/.gemini/antigravity/skills/` |
| OpenCode | `.agents/skills/` | `~/.config/opencode/skills/` |
| Windsurf | `.windsurf/skills/` | `~/.codeium/windsurf/skills/` |
| GitHub Copilot | `.agents/skills/` | `~/.copilot/skills/` |

### 方式一：安装脚本（推荐）

适用于离线或内网环境；将叶子 Skill 软链接至目标目录。

```bash
cd BioLens-Skill/spatial_single-cell
chmod +x ./install-to-agent.sh

# 当前项目（以 Cursor 为例）
./install-to-agent.sh --agent cursor

# 其他 Agent
./install-to-agent.sh --agent claude
./install-to-agent.sh --agent codex /path/to/project

# 用户全局目录
./install-to-agent.sh --agent cursor --global
./install-to-agent.sh --agent claude --global

# 直接指定目标路径
./install-to-agent.sh /path/to/project/.claude/skills
./install-to-agent.sh ~/.codex/skills
```

安装脚本会链接全部含 `SKILL.md` 的叶子目录，并同步链接 `requirements.txt`。

### 方式二：手动复制

```bash
DEST=/path/to/project/.cursor/skills   # 请替换为上表对应路径
mkdir -p "$DEST"
for d in BioLens-Skill/spatial_single-cell/*/; do
  name=$(basename "$d")
  [[ -f "$d/SKILL.md" ]] || continue
  cp -R "$d" "$DEST/$name"
done
cp BioLens-Skill/spatial_single-cell/requirements.txt "$DEST/"
```

仅安装单个 Skill：

```bash
cp -R BioLens-Skill/spatial_single-cell/scanpy-cluster \
  /path/to/project/.cursor/skills/scanpy-cluster
```

### 方式三：`npx skills add`（需 Node.js）

兼容 [vercel-labs/skills](https://github.com/vercel-labs/skills) 生态：

```bash
npx skills add CNGBdb-org/BioLens-Skill --list
npx skills add CNGBdb-org/BioLens-Skill --skill scanpy-cluster -a cursor
npx skills add CNGBdb-org/BioLens-Skill --skill spatial-svg -a claude-code -a codex -y
npx skills add CNGBdb-org/BioLens-Skill --skill geo-sra -a cursor -g -y
```

完成后请在本机执行：`pip install -r BioLens-Skill/spatial_single-cell/requirements.txt`。

---

## Skill 一览

| Skill | Depth | 说明 |
|-------|-------|------|
| `geo-sra` | L1–L2 | NCBI GEO / SRA / BioProject 公开单细胞与空间数据发现 |
| `sc-ingest` | L5 | scRNA 矩阵摄取（h5ad / 10x h5 / mtx）→ 统一 AnnData |
| `scanpy-qc` | L5 | 基因数 / mito 等 QC 过滤与小提琴图 |
| `scanpy-preprocess` | L5 | normalize、log1p、HVG、scale、PCA |
| `scanpy-cluster` | L5 | neighbors、UMAP、Leiden 聚类 |
| `scanpy-markers` | L5 | 按 cluster 的 wilcoxon marker 排序 |
| `sc-multi-integrate` | L5 | 多数据集 concat + Combat + 批次混匀报告 |
| `scvi-integrate` | L5 | scVI 批次整合（无包时降级 Combat/PCA） |
| `spatial-ingest` | L5 | 空间转录组摄取（要求 `obsm['spatial']`） |
| `spatial-qc` | L5 | 空间 counts/genes 指标与 QC 图 |
| `spatial-svg` | L5 | Moran I / Squidpy 空间可变基因 |
| `spatial-deconv` | L5 | NMF 基线 spot 细胞组成解卷积 |
| `spatial-interaction` | L5 | 邻域标签共现 / 互作富集 |

## 流水线关系

```text
geo-sra（可选：公开数据发现）
  │
  ├─ scRNA 主线
  │    sc-ingest → scanpy-qc → scanpy-preprocess
  │         → scanpy-cluster → scanpy-markers
  │         → sc-multi-integrate / scvi-integrate
  │
  └─ 空间主线（需 obsm['spatial']）
       spatial-ingest → spatial-qc
            → spatial-svg | spatial-deconv | spatial-interaction
```

- 数据发现：`geo-sra`（只给元数据与下载路径，不做本地分析）
- scRNA 主线：`sc-ingest` → `scanpy-qc` → `scanpy-preprocess` → `scanpy-cluster` → `scanpy-markers`
- 多样本整合：`sc-multi-integrate`（轻量）或 `scvi-integrate`（深度，可选）
- 空间主线：`spatial-ingest` → `spatial-qc` → `spatial-svg` / `spatial-deconv` / `spatial-interaction`

## 使用示例

各 Skill 的详细用法见对应目录下的 `SKILL.md`。下列命令均在对应叶子 Skill 目录下执行；多数分析 Skill 支持 `--demo` 生成冒烟数据。

| Skill | 示例命令 |
|-------|----------|
| `geo-sra` | `python ./scripts/query.py search "PBMC COVID" --limit 10` |
| `sc-ingest` | `python ./scripts/query.py demo -o ./out` |
| `scanpy-qc` | `python ./scripts/query.py data.h5ad -o ./out` |
| `scanpy-preprocess` | `python ./scripts/query.py qc.h5ad -o ./out` |
| `scanpy-cluster` | `python ./scripts/query.py preprocessed.h5ad -o ./out` |
| `scanpy-markers` | `python ./scripts/query.py clustered.h5ad -o ./out` |
| `sc-multi-integrate` | `python ./scripts/query.py demo -o ./out` |
| `scvi-integrate` | `python ./scripts/query.py multi.h5ad --batch-key batch -o ./out` |
| `spatial-ingest` | `python ./scripts/query.py demo -o ./out` |
| `spatial-qc` | `python ./scripts/query.py spatial.h5ad -o ./out` |
| `spatial-svg` | `python ./scripts/query.py spatial.h5ad -o ./out` |
| `spatial-deconv` | `python ./scripts/query.py spatial.h5ad -o ./out` |
| `spatial-interaction` | `python ./scripts/query.py spatial.h5ad --label-key cluster -o ./out` |

### 自然语言触发示例

安装至 Agent 后，可按下列问法路由至对应 Skill：

| # | 示例问法 | 对应 Skill |
|---|----------|------------|
| 1 | 有没有人肝脏单细胞 RNA-seq 的 GEO？GSE149614 原始数据怎么下？ | `geo-sra` |
| 2 | 把这份 10x 矩阵读成 h5ad。 | `sc-ingest` |
| 3 | 对这个 h5ad 做 QC，按 mito 过滤细胞。 | `scanpy-qc` |
| 4 | 标准化并选高变基因，做 PCA 预处理。 | `scanpy-preprocess` |
| 5 | 做 Leiden 聚类并画 UMAP。 | `scanpy-cluster` |
| 6 | 找出各群 marker 基因。 | `scanpy-markers` |
| 7 | 几个数据集合在一起做去批次，并给批次混匀报告。 | `sc-multi-integrate` |
| 8 | 用 scVI 做批次整合。 | `scvi-integrate` |
| 9 | 读入 Visium h5ad / 生成空间 demo 数据。 | `spatial-ingest` |
| 10 | 做空间质控，画 Visium QC 图。 | `spatial-qc` |
| 11 | 找空间可变基因（Moran I / SVG）。 | `spatial-svg` |
| 12 | 对 spot 做 NMF 空间解卷积，估计细胞组成。 | `spatial-deconv` |
| 13 | 谁和谁空间相邻？输出邻域共现矩阵。 | `spatial-interaction` |
