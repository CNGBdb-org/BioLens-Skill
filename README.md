# BioLens-Skill

CIMA / TrueBlood **Agent Skills**（CNGBdb BioLens）。仓库：https://github.com/CNGBdb-org/BioLens-Skill

```text
BioLens-Skill/
├── install-to-agent.sh   # 安装到 Cursor / Claude / Codex …
├── README.md
└── cima/                 # 分类目录（12 个叶子 Skill + demo）
    ├── README.md
    ├── demo/
    ├── cima-resource/
    ├── cima-atlas-explore/
    ├── cima-scrna-preprocessing/
    └── …
```

安装后形态：`<skills-dir>/<skill-name>/SKILL.md`（Agent 只认展平后的叶子目录）。

---

## 安装方式

### 主流 Agent 路径

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

### 方式一：安装脚本（推荐，离线/内网友好）

```bash
git clone https://github.com/CNGBdb-org/BioLens-Skill.git
cd BioLens-Skill
chmod +x ./install-to-agent.sh

# 装到当前项目（Cursor）
./install-to-agent.sh --agent cursor
./install-to-agent.sh --agent cursor --category cima

# 其他 Agent
./install-to-agent.sh --agent claude
./install-to-agent.sh --agent codex /path/to/project

# 用户全局
./install-to-agent.sh --agent cursor --global
./install-to-agent.sh --agent claude --global --category cima

# 或直接指定目标目录
./install-to-agent.sh /path/to/project/.claude/skills
./install-to-agent.sh ~/.codex/skills --category cima
```

脚本会把 `cima/<name>/` **软链**到目标目录下的 `<name>/`。

### 方式二：手动拷贝

```bash
git clone https://github.com/CNGBdb-org/BioLens-Skill.git
DEST=/path/to/project/.cursor/skills   # 换成上表路径
mkdir -p "$DEST"
for d in BioLens-Skill/cima/cima-*/; do
  name=$(basename "$d")
  [[ -f "$d/SKILL.md" ]] || continue
  cp -R "$d" "$DEST/$name"
done
```

只装一个 Skill：

```bash
cp -R BioLens-Skill/cima/cima-scrna-preprocessing /path/to/project/.cursor/skills/cima-scrna-preprocessing
```

### 方式三：通用 CLI `npx skills add`（需 Node.js）

与 [vercel-labs/skills](https://github.com/vercel-labs/skills) 生态兼容：

```bash
npx skills add CNGBdb-org/BioLens-Skill --list
npx skills add CNGBdb-org/BioLens-Skill --skill cima-scrna-preprocessing -a cursor
npx skills add CNGBdb-org/BioLens-Skill --skill cima-xqtl -a claude-code -a codex -y
npx skills add CNGBdb-org/BioLens-Skill --skill cima-clm -a cursor -g -y
```

### 依赖

各叶子 Skill 依赖见对应 `cima/<name>/SKILL.md`。常见：`scanpy` / `anndata`；可选 `statsmodels`、`harmony-pytorch` / `harmonypy`、`cosg`。

---

## Skill 一览

| Skill | Depth | 用途 |
|-------|-------|------|
| `cima-resource` | L3 | CIMA 数据清单 / 本地路径 |
| `cima-atlas-explore` | L4 | 门户图谱浏览：视图 / donor / 组成 / 基因 UMAP |
| `cima-scrna-preprocessing` | L5 | scRNA QC → 聚类 → 系群拆分 |
| `cima-cell-annotation` | L5 | TrueBlood marker 签名 → L1–L4 |
| `cima-pseudobulk-variance` | L5 | Pseudobulk 聚合 + 方差分解 |
| `cima-scratac-preprocessing` | L5 | scATAC peak 预处理 + gene activity |
| `cima-multiomics-integration` | L5 | scRNA+scATAC 整合 |
| `cima-metacell` | L5 | Metacell 聚合（CPU） |
| `cima-grn-scenicplus` | L4 | 预计算 eRegulon / GRN 查询 |
| `cima-xqtl` | L4 | 预计算 cis-xQTL 查询 |
| `cima-smr-gwas` | L4 | 预计算 SMR/GWAS 查询 |
| `cima-clm` | L5 | CLM in silico 变异效应 demo |

流水线关系、demo 命令与自然语言触发示例见 [`cima/README.md`](cima/README.md)、[`cima/demo/README.md`](cima/demo/README.md)。
