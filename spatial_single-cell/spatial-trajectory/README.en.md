# spatial-trajectory


## Runtime

```bash
cd skills/spatial/spatial-trajectory
python ./scripts/query.py <h5ad> [-o outdir] [--root CELL_ID]
```

Bundled: `scverse_common/` (this directory)

Compute diffusion pseudotime (DPT) or PCA-rank fallback on spatial AnnData and plot spatial trajectory. Use for differentiation/ordering along tissue. Not for multi-slice registration (use spatial-register) or SVG (use spatial-svg).

```bash
python ./scripts/query.py spatial.h5ad -o out/traj
python ./scripts/query.py --demo -o out/traj_demo
```
