# 变异综合解读（编排）

跨库科研辅助链路：**dbsnp → gnomad → clinvar**。不替代单库精确查询，也不替代临床 ACMG 终判。

## 何时用

- 「这个变异怎么综合看 / 解读」
- 同时要坐标、人群频率、ClinVar 意义

只要单点信息时请用：`dbsnp` / `gnomad` / `clinvar`。

## 运行

```bash
cd skills/genomics/variant-interpretation
python ./scripts/query.py --rsid rs80357906
python ./scripts/query.py --rsid rs80357906 --format json
python ./scripts/query.py --hgvs 'NC_000017.11:g.43057063dup'
python ./scripts/query.py --chrom 17 --pos 43057063
```

需与 `dbsnp`、`gnomad`、`clinvar` 同处于 `skills/` 下。依赖见 `skills/requirements.txt`。
