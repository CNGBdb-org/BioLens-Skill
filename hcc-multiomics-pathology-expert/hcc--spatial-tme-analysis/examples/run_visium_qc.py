#!/usr/bin/env python3
"""Run dependency-light QC for one 10x Visium sample directory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

EXPERT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(EXPERT_ROOT / "scripts"))
from tenx_visium import find_visium_files, load_10x_h5, load_positions, load_scalefactors, mitochondrial_mask  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-dir", required=True, type=Path)
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    matrix_path, position_path, scale_path = find_visium_files(args.sample_dir)
    matrix, barcodes, genes = load_10x_h5(matrix_path)
    positions = load_positions(position_path)
    mt_mask = mitochondrial_mask(genes)
    total = np.asarray(matrix.sum(axis=1)).ravel()
    detected = np.diff(matrix.indptr)
    mt_total = np.asarray(matrix[:, mt_mask].sum(axis=1)).ravel() if mt_mask.any() else np.zeros(matrix.shape[0])
    rows = []
    for index, barcode in enumerate(barcodes):
        in_tissue, pxl_col, pxl_row = positions.get(barcode, (0, np.nan, np.nan))
        rows.append({"sample_id": args.sample_id, "barcode": barcode, "in_tissue": in_tissue, "pxl_col": pxl_col, "pxl_row": pxl_row, "total_counts": int(total[index]), "detected_genes": int(detected[index]), "pct_mt": float(100 * mt_total[index] / total[index]) if total[index] else 0.0})
    qc = pd.DataFrame(rows)
    tissue = qc[qc["in_tissue"] == 1]
    summary = {
        "sample_id": args.sample_id,
        "spot_count": len(qc),
        "in_tissue_spot_count": len(tissue),
        "gene_count": len(genes),
        "median_counts_in_tissue": float(tissue["total_counts"].median()) if len(tissue) else 0.0,
        "median_genes_in_tissue": float(tissue["detected_genes"].median()) if len(tissue) else 0.0,
        "median_pct_mt_in_tissue": float(tissue["pct_mt"].median()) if len(tissue) else 0.0,
        "coordinate_coverage": float(qc[["pxl_col", "pxl_row"]].notna().all(axis=1).mean()),
        "scalefactors": load_scalefactors(scale_path),
    }
    args.output.mkdir(parents=True, exist_ok=True)
    qc.to_csv(args.output / "spatial_qc.tsv", sep="\t", index=False)
    (args.output / "spatial_qc_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output / "spatial_qc_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
