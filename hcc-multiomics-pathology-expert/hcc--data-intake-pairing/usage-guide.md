# 使用指南：数据接入与配对

适用于“这些 HCC 文件能做什么”“病理和 RNA 能否配对”“建立项目 manifest”。

首次执行代码前先运行 `python scripts/bootstrap.py --output <run>/preflight.json`。该命令只检查依赖；缺包时由 Agent 说明影响并获得用户确认后，才在独立虚拟环境安装对应 profile。

没有 manifest 时，用下面的命令先生成草案；它不会猜测患者、分组或配对关系：

```text
python examples/draft_manifest.py --input <data-folder> --output task/sample_manifest_draft.tsv
```

```text
python examples/inspect_manifest.py --manifest sample_manifest.tsv --output task/00_intake
```

先提供 manifest；没有时先从文件名建立草案并把所有推断字段标为待确认。输出不代表正式分析授权。TCGA WSI+RNA 默认只给患者级配对，只有明确 `block_id` 或切片衍生关系才可提升。

工作区已有 GSE238264 原始归档时，可先生成保守的空间 manifest：

```text
python examples/create_gse238264_manifest.py --input-dir data/GSE238264 --output task/sample_manifest.tsv
```

该样例仅写入 GEO 已公布的 7 例 HCC 响应分组及归档内样本路径；不会推断病理边界、临床协变量或跨模态配对。
