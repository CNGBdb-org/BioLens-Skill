# CIMA Pipeline Skills

CIMA / TrueBlood **本地流水线与独立查询 Skill**（[BioLens-Skill](https://github.com/CNGBdb-org/BioLens-Skill)）。本目录共 **12** 个叶子 Skill。

```text
cima/
├── install-to-agent.sh
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
cd BioLens-Skill/cima
chmod +x ./install-to-agent.sh

# 装到当前项目（Cursor）
./install-to-agent.sh --agent cursor

# 其他 Agent
./install-to-agent.sh --agent claude
./install-to-agent.sh --agent codex /path/to/project

# 用户全局
./install-to-agent.sh --agent cursor --global
./install-to-agent.sh --agent claude --global

# 或直接指定目标目录
./install-to-agent.sh /path/to/project/.claude/skills
./install-to-agent.sh ~/.codex/skills
```

脚本会把本目录下各 `cima-*/` **软链**到目标目录下的同名叶子。

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

各叶子 Skill 依赖见对应 `<name>/SKILL.md`。常见：`scanpy` / `anndata`；可选 `statsmodels`、`harmony-pytorch` / `harmonypy`、`cosg`。

---

## Skill 一览

| Skill | Depth | 用途 |
|-------|-------|------|
| `cima-resource` | L3 | CIMA 数据清单 / 本地路径（部署：`/public/.../CIMA_Resource`；外网门户·FTP） |
| `cima-atlas-explore` | L4 | 门户图谱浏览：视图 / donor / 组成 / 基因 UMAP（不含 GRN·xQTL·SMR·清单） |
| `cima-scrna-preprocessing` | L5 | scRNA QC → 聚类 → 系群拆分 |
| `cima-cell-annotation` | L5 | TrueBlood marker 签名 → L1–L4（73 leaf） |
| `cima-pseudobulk-variance` | L5 | Pseudobulk 聚合 + 方差分解 |
| `cima-scratac-preprocessing` | L5 | scATAC peak 预处理 + 可选 gene activity（CPU） |
| `cima-multiomics-integration` | L5 | scRNA+scATAC 整合（ATAC 可为 peak 或 gene） |
| `cima-metacell` | L5 | Metacell 聚合（CPU，无 SEACells） |
| `cima-grn-scenicplus` | L4 | 预计算 eRegulon / GRN 查询（独立，不依赖 explore `cima`） |
| `cima-xqtl` | L4 | 预计算 cis-xQTL 查询（独立） |
| `cima-smr-gwas` | L4 | 预计算 SMR/GWAS 查询（独立） |
| `cima-clm` | L5 | CLM in silico 变异效应 demo（预计算结果） |

## 流水线关系

- 图谱浏览：`cima-atlas-explore`（视图 / donor / UMAP；清单与 GRN/xQTL/SMR 见专用 Skill）
- scRNA 主线：`cima-scrna-preprocessing` → `cima-cell-annotation` → `cima-pseudobulk-variance` → `cima-xqtl` / `cima-smr-gwas`
- 多组学主线：… → `cima-scratac-preprocessing` → `cima-multiomics-integration` → `cima-metacell` → `cima-grn-scenicplus`
- 独立：`cima-resource`、`cima-clm`

## 使用示例

每个 Skill 的 `SKILL.md` 均有 **Examples**。本目录提供合成 demo（仅冒烟，非论文复现）：

| 文件 | 用途 |
|------|------|
| [`demo/paired_demo_rna.h5ad`](demo/paired_demo_rna.h5ad) | **推荐** scRNA（与 ATAC 共享 8 donor）→ Steps 1–3 / 5–6 |
| [`demo/paired_demo_atac.h5ad`](demo/paired_demo_atac.h5ad) | **推荐** scATAC peaks → Step 4（可出 gene activity） |
| [`demo/paired_demo_atac_gene.h5ad`](demo/paired_demo_atac_gene.h5ad) | **推荐** gene-level ATAC → 直喂 Step 5 |
| `demo/demo_nk_raw.h5ad` + `demo/demo_atac_raw.h5ad` | 更小；样本不重叠 → Step6 配对为 0 |

完整 Steps 1–6 命令见 [`demo/README.md`](demo/README.md)。下面是命令速查（路径相对叶子 Skill，demo 在 `../demo/`）。

| Skill | 一键示例 |
|-------|----------|
| `cima-resource` | `python ./scripts/cima_resource_lookup.py overview` |
| `cima-atlas-explore` | `python ./scripts/query.py catalog list_datasets` |
| `cima-scrna-preprocessing` | `python ./scripts/cima_scrna_preprocessing_cpu.py --input ../demo/paired_demo_rna.h5ad --output ./out --hvg-n 1500 --skip-subsampling` |
| `cima-cell-annotation` | `python ./scripts/cima_cell_annotation_cpu.py --input Annotation_1st_fullgenes.h5ad --output ./out --lineage all` |
| `cima-pseudobulk-variance` | `python ./scripts/cima_pseudobulk_variance_cpu.py --input Annotation_1st.h5ad --output ./out --covariates age sex` |
| `cima-scratac-preprocessing` | `python ./scripts/cima_scratac_cpu.py --input ../demo/paired_demo_atac.h5ad --output ./out --rna rna.h5ad` |
| `cima-multiomics-integration` | `python ./scripts/cima_multiomics_integration_cpu.py --rna rna.h5ad --atac ../demo/paired_demo_atac_gene.h5ad --output ./out` |
| `cima-metacell` | `python ./scripts/cima_metacell_cpu.py --rna rna.h5ad --atac atac_labeled.h5ad --output ./out` |
| `cima-grn-scenicplus` | `bash ./scripts/grn.sh grn_lookup --tf FOXP3 --max 20` |
| `cima-xqtl` | `bash ./scripts/xqtl.sh --gene CDC42 --max 20` |
| `cima-smr-gwas` | `bash ./scripts/smr.sh --gene ARL14EP --max 10` |
| `cima-clm` | `python ./scripts/run_demo.py /path/to/CIMA-CLM_Demo --out ./clm_out` |

### Agent 侧怎么触发（自然语言示例）

| # | 用户说法（示例） | 触发 Skill |
|---|------------------|------------|
| 0 | CIMA 有哪些数据？在哪？/ TrueBlood resource 本地路径 / NK h5ad 在哪 | `cima-resource` |
| 0b | CIMA 有哪些视图？/ B 视图画 CD8A UMAP / donor 临床表 | `cima-atlas-explore` |
| 1 | 按 CIMA 流程预处理这个 PBMC h5ad / 对 raw counts 做 QC 聚类再按系群拆分 | `cima-scrna-preprocessing` |
| 2 | 对 CIMA Annotation_1st 做系群子聚类 + L1–L4 marker 签名注释 | `cima-cell-annotation` |
| 3 | 按 sample×celltype 做 pseudobulk，看看 age/sex 各解释多少方差 | `cima-pseudobulk-variance` |
| 4 | 没有 GPU，用 CPU 预处理这个 scATAC peak 矩阵 | `cima-scratac-preprocessing` |
| 5 | 把 scRNA 的细胞类型迁到 scATAC（不用 SCGLUE） | `cima-multiomics-integration` |
| 6 | SEACells 装不了，用 CPU 做 CIMA metacell | `cima-metacell` |
| 7 | FOXP3 在 CIMA 里调控哪些基因？/ 列一下 B 系群 eRegulon | `cima-grn-scenicplus` |
| 8 | 查 CDC42 的 cis-eQTL / Bn_TCL1A 的 cis-caQTL | `cima-xqtl` |
| 9 | ARL14EP（或某基因）在 CIMA SMR 里有哪些免疫疾病关联？ | `cima-smr-gwas` |
| 10 | 跑一下 CIMA-CLM in silico mutagenesis demo | `cima-clm` |
