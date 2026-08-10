# CIMA Pipeline Skills

面向 [CIMA / TrueBlood](https://db.cngb.org/trueblood/cima/)（Chinese Immune Multi-Omics Atlas）的 Agent Skills 集合，收录于 [BioLens-Skill](https://github.com/CNGBdb-org/BioLens-Skill)。本目录包含 **12** 个可独立安装的叶子 Skill，覆盖数据资源定位、门户图谱浏览、预计算查询，以及本地分析流水线。

文献：Yin et al., *Science* 2026；DOI [10.1126/science.adt3130](https://doi.org/10.1126/science.adt3130)

```text
cima/
├── install-to-agent.sh   # 安装至各类 Agent
├── requirements.txt      # Python 依赖
├── README.md
├── demo/                 # 合成演示数据（非论文复现）
├── cima-resource/
├── cima-atlas-explore/
├── cima-scrna-preprocessing/
└── …
```

安装完成后，Agent 侧目录形态为：`<skills-dir>/<skill-name>/SKILL.md`。

---

## 安装

### Python 依赖

```bash
git clone https://github.com/CNGBdb-org/BioLens-Skill.git
cd BioLens-Skill/cima
python -m pip install -r requirements.txt
```

该依赖清单覆盖资源查询、图谱浏览、GRN / xQTL / SMR 查询，以及基于 Scanpy 的流水线 Skill。可选组件（如 `harmonypy`、`cosg`、`logomaker`）见 `requirements.txt` 末尾注释；各 Skill 的兼容性说明亦见对应 `SKILL.md`。

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
cd BioLens-Skill/cima
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

安装脚本会链接全部 `cima-*/` 叶子目录，并同步链接 `requirements.txt`。

### 方式二：手动复制

```bash
DEST=/path/to/project/.cursor/skills   # 请替换为上表对应路径
mkdir -p "$DEST"
for d in BioLens-Skill/cima/cima-*/; do
  name=$(basename "$d")
  [[ -f "$d/SKILL.md" ]] || continue
  cp -R "$d" "$DEST/$name"
done
cp BioLens-Skill/cima/requirements.txt "$DEST/"
```

仅安装单个 Skill：

```bash
cp -R BioLens-Skill/cima/cima-scrna-preprocessing \
  /path/to/project/.cursor/skills/cima-scrna-preprocessing
```

### 方式三：`npx skills add`（需 Node.js）

兼容 [vercel-labs/skills](https://github.com/vercel-labs/skills) 生态：

```bash
npx skills add CNGBdb-org/BioLens-Skill --list
npx skills add CNGBdb-org/BioLens-Skill --skill cima-scrna-preprocessing -a cursor
npx skills add CNGBdb-org/BioLens-Skill --skill cima-xqtl -a claude-code -a codex -y
npx skills add CNGBdb-org/BioLens-Skill --skill cima-clm -a cursor -g -y
```

完成后请在本机执行：`pip install -r BioLens-Skill/cima/requirements.txt`。

---

## Skill 一览

| Skill | Depth | 说明 |
|-------|-------|------|
| `cima-resource` | L3 | CIMA / TrueBlood 可下载资源清单与公开 FTP 位置 |
| `cima-atlas-explore` | L4 | 门户图谱浏览（视图、donor、组成、基因 UMAP） |
| `cima-scrna-preprocessing` | L5 | scRNA 质控、聚类与系群拆分 |
| `cima-cell-annotation` | L5 | TrueBlood marker 签名注释（L1–L4，73 leaf） |
| `cima-pseudobulk-variance` | L5 | Pseudobulk 聚合与方差分解 |
| `cima-scratac-preprocessing` | L5 | scATAC peak 预处理（可选 gene activity，CPU） |
| `cima-multiomics-integration` | L5 | scRNA 与 scATAC 整合（ATAC 可为 peak 或 gene activity） |
| `cima-metacell` | L5 | Metacell 聚合（CPU，不依赖 SEACells） |
| `cima-grn-scenicplus` | L4 | 预计算 eRegulon / GRN 查询 |
| `cima-xqtl` | L4 | 预计算 cis-xQTL 查询 |
| `cima-smr-gwas` | L4 | 预计算 SMR / GWAS 关联查询 |
| `cima-clm` | L5 | CIMA-CLM in silico 变异效应演示（预计算结果） |

公开数据目录：

- FTP：https://ftp.cngb.org/pub/SciRAID/trueblood/cima/CIMA_Resource/
- 门户：https://db.cngb.org/trueblood/cima/resource

## 流水线关系

- 资源定位：`cima-resource`
- 图谱浏览：`cima-atlas-explore`
- scRNA 主线：`cima-scrna-preprocessing` → `cima-cell-annotation` → `cima-pseudobulk-variance` → `cima-xqtl` / `cima-smr-gwas`
- 多组学主线：`cima-scratac-preprocessing` → `cima-multiomics-integration` → `cima-metacell` → `cima-grn-scenicplus`
- 独立模块：`cima-clm`

## 使用示例

各 Skill 的详细用法见对应目录下的 `SKILL.md`。`demo/` 提供合成演示数据，仅用于流程验证，不构成论文结果复现。

| 文件 | 说明 |
|------|------|
| [`demo/paired_demo_rna.h5ad`](demo/paired_demo_rna.h5ad) | 配对 scRNA（与 ATAC 共享 8 个 donor） |
| [`demo/paired_demo_atac.h5ad`](demo/paired_demo_atac.h5ad) | 配对 scATAC peaks |
| [`demo/paired_demo_atac_gene.h5ad`](demo/paired_demo_atac_gene.h5ad) | 配对 gene-level ATAC |
| `demo/demo_nk_raw.h5ad`、`demo/demo_atac_raw.h5ad` | 更小规模演示集（样本不重叠） |

完整 Steps 1–6 命令见 [`demo/README.md`](demo/README.md)。下列命令均在对应叶子 Skill 目录下执行，演示数据路径为 `../demo/`。

| Skill | 示例命令 |
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

### 自然语言触发示例

安装至 Agent 后，可按下列问法路由至对应 Skill：

| # | 示例问法 | 对应 Skill |
|---|----------|------------|
| 1 | CIMA 有哪些可下载数据？TrueBlood Resource 在哪里？NK 的 scRNA h5ad 如何获取？ | `cima-resource` |
| 2 | CIMA 门户有哪些谱系视图？请在 B 视图绘制 CD8A 的 UMAP，并查看 donor 临床信息。 | `cima-atlas-explore` |
| 3 | 请按 CIMA 流程对这份 PBMC h5ad 做质控、聚类，并按系群拆分。 | `cima-scrna-preprocessing` |
| 4 | 请对 Annotation_1st 结果做系群子聚类，并用 L1–L4 marker 签名进行注释。 | `cima-cell-annotation` |
| 5 | 请按 sample × cell type 聚合为 pseudobulk，并估计 age / sex 对表达方差的贡献。 | `cima-pseudobulk-variance` |
| 6 | 请在 CPU 环境下预处理该 scATAC peak 矩阵。 | `cima-scratac-preprocessing` |
| 7 | 请将 scRNA 细胞类型标签迁移至配对的 scATAC 数据。 | `cima-multiomics-integration` |
| 8 | 请在 CPU 环境下完成 CIMA metacell 聚合。 | `cima-metacell` |
| 9 | FOXP3 在 CIMA 中调控哪些下游基因？请列出 B 系群相关 eRegulon。 | `cima-grn-scenicplus` |
| 10 | 请查询 CDC42 的 cis-eQTL，以及 Bn_TCL1A 的 cis-caQTL。 | `cima-xqtl` |
| 11 | 请查询某基因（如 ARL14EP）在 CIMA SMR 结果中与哪些免疫相关性状关联。 | `cima-smr-gwas` |
| 12 | 请运行 CIMA-CLM in silico mutagenesis 演示。 | `cima-clm` |
