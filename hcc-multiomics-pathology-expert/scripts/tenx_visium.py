"""Small, dependency-light 10x Visium readers shared by HCC Expert examples."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import h5py
import numpy as np
from scipy import sparse


def _decode(values: object) -> list[str]:
    return [item.decode("utf-8") if isinstance(item, bytes) else str(item) for item in values]


def load_10x_h5(path: Path) -> tuple[sparse.csr_matrix, list[str], list[str]]:
    with h5py.File(path, "r") as handle:
        matrix = handle["matrix"]
        data = matrix["data"][()]
        indices = matrix["indices"][()]
        indptr = matrix["indptr"][()]
        shape = tuple(int(item) for item in matrix["shape"][()])
        barcodes = _decode(matrix["barcodes"][()])
        features = matrix["features"]
        names = _decode(features["name"][()])
    return sparse.csc_matrix((data, indices, indptr), shape=shape).T.tocsr(), barcodes, names


def load_positions(path: Path) -> dict[str, tuple[int, float, float]]:
    positions: dict[str, tuple[int, float, float]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.reader(handle):
            if len(row) < 6 or row[0] in {"barcode", ""}:
                continue
            try:
                positions[row[0]] = (int(float(row[1])), float(row[5]), float(row[4]))
            except ValueError:
                continue
    return positions


def load_scalefactors(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def find_visium_files(sample_dir: Path) -> tuple[Path, Path, Path]:
    matrix = sample_dir / "filtered_feature_bc_matrix.h5"
    positions = sample_dir / "spatial" / "tissue_positions_list.csv"
    if not positions.exists():
        positions = sample_dir / "spatial" / "tissue_positions.csv"
    scalefactors = sample_dir / "spatial" / "scalefactors_json.json"
    if not matrix.exists() or not positions.exists():
        raise FileNotFoundError("expected filtered_feature_bc_matrix.h5 and tissue position CSV")
    return matrix, positions, scalefactors


def mitochondrial_mask(gene_names: list[str]) -> np.ndarray:
    return np.array([name.upper().startswith("MT-") for name in gene_names], dtype=bool)
