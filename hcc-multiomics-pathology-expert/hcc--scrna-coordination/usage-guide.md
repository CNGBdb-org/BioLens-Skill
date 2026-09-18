# 使用指南：交接给单细胞专家

```text
python examples/create_handoff.py --input query.h5ad --output task/handoff.json --objective "注释 HCC TME"
```

将 `handoff.json` 与用户目标交给 `scrna-seq-expert`。首版为显式交接，不假设平台存在自动跨 Expert API。返回对象缺少原始 counts、患者标识或注释置信度时，不能进入细胞组成定量和通讯解释。
