# spatial-register


## Runtime

```bash
cd skills/spatial/spatial-register
python ./scripts/query.py run <h5ad1> <h5ad2> [more...] [-o outdir]
```

Bundled: `scverse_common/` (this directory)

Align multiple spatial slices into a common coordinate frame (Procrustes on expression landmarks; PASTE if available). Use before spatial-integrate for multi-slice. Not for expression batch correction alone (use spatial-integrate).

```bash
python ./scripts/query.py demo -o out/register
python ./scripts/query.py run s1.h5ad s2.h5ad -o out/register
```
