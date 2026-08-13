# spatial-integrate


## Runtime

```bash
cd skills/spatial/spatial-integrate
python ./scripts/query.py <h5ad> [-o outdir] [--batch-key batch]
```

Bundled: `scverse_common/` (this directory)

Integrate multi-sample spatial AnnData (Harmony if installed else Combat/PCA). Needs obs batch or slice. Use after spatial-register or concat. Not for coordinate alignment (use spatial-register) or scRNA-only integrate (use sc-multi-integrate / scvi-integrate).

```bash
python ./scripts/query.py multi.h5ad -o out/integ --batch-key slice
python ./scripts/query.py --demo -o out/integ_demo
```
