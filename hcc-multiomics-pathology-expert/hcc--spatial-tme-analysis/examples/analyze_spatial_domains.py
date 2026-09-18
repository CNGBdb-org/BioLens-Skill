#!/usr/bin/env python3
"""Discover candidate Visium domains and score HCC programs without Scanpy."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.cluster.vq import kmeans2
from scipy.sparse.linalg import svds

EXPERT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(EXPERT_ROOT / "scripts"))
from tenx_visium import find_visium_files, load_10x_h5, load_positions  # noqa: E402


PROGRAMS = {
    "epithelial_tumor_candidate": ["AFP", "GPC3", "EPCAM", "KRT8", "KRT18", "KRT19"],
    "immune": ["PTPRC", "CD3D", "TRBC2", "NKG7", "LST1"],
    "myeloid": ["LYZ", "C1QA", "C1QB", "APOE", "FCER1G"],
    "fibroblast_ecm": ["COL1A1", "COL1A2", "COL3A1", "DCN", "LUM"],
    "endothelial": ["KDR", "EMCN", "PECAM1", "VWF", "ENG"],
    "hypoxia_glycolysis": ["CA9", "VEGFA", "SLC2A1", "LDHA", "ENO1"],
}


def log_normalize(matrix: sparse.csr_matrix) -> sparse.csr_matrix:
    total = np.asarray(matrix.sum(axis=1)).ravel()
    factors = np.divide(1e4, total, out=np.zeros_like(total, dtype=float), where=total > 0)
    normalized = sparse.diags(factors) @ matrix.astype(float)
    normalized.data = np.log1p(normalized.data)
    return normalized.tocsr()


def top_variable_genes(matrix: sparse.csr_matrix, maximum: int = 2000) -> np.ndarray:
    mean = np.asarray(matrix.mean(axis=0)).ravel()
    mean_sq = np.asarray(matrix.multiply(matrix).mean(axis=0)).ravel()
    variance = np.maximum(mean_sq - mean**2, 0)
    count = min(maximum, matrix.shape[1])
    return np.argpartition(variance, -count)[-count:]


def component_scores(matrix: sparse.csr_matrix) -> np.ndarray:
    variables = top_variable_genes(matrix)
    subset = matrix[:, variables]
    components = min(20, subset.shape[0] - 1, subset.shape[1] - 1)
    if components < 2:
        raise ValueError("too few spots or variable genes for domain discovery")
    u, singular_values, _ = svds(subset, k=components)
    order = np.argsort(singular_values)[::-1]
    return u[:, order] * singular_values[order]


def program_scores(matrix: sparse.csr_matrix, genes: list[str]) -> tuple[dict[str, np.ndarray], dict[str, list[str]]]:
    index = {gene.upper(): number for number, gene in enumerate(genes)}
    scores: dict[str, np.ndarray] = {}
    detected: dict[str, list[str]] = {}
    for program, requested in PROGRAMS.items():
        found = [gene for gene in requested if gene in index]
        detected[program] = found
        if found:
            scores[program] = np.asarray(matrix[:, [index[gene] for gene in found]].mean(axis=1)).ravel()
        else:
            scores[program] = np.zeros(matrix.shape[0])
    return scores, detected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample-dir", required=True, type=Path)
    parser.add_argument("--sample-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--n-domains", type=int, default=6)
    args = parser.parse_args()
    matrix_path, position_path, _ = find_visium_files(args.sample_dir)
    matrix, barcodes, genes = load_10x_h5(matrix_path)
    positions = load_positions(position_path)
    mask = np.array([positions.get(barcode, (0, np.nan, np.nan))[0] == 1 for barcode in barcodes])
    if mask.sum() < args.n_domains:
        raise SystemExit("fewer in-tissue spots than requested domains")
    normalized = log_normalize(matrix[mask])
    scores = component_scores(normalized)
    _, labels = kmeans2(scores, k=args.n_domains, minit="++", seed=0)
    programs, detected = program_scores(normalized, genes)
    rows = []
    for number, barcode in enumerate(np.array(barcodes)[mask]):
        _, pxl_col, pxl_row = positions[barcode]
        row = {"sample_id": args.sample_id, "barcode": barcode, "pxl_col": pxl_col, "pxl_row": pxl_row, "candidate_domain": int(labels[number])}
        row.update({name: float(values[number]) for name, values in programs.items()})
        rows.append(row)
    domains = pd.DataFrame(rows)
    summary = {
        "sample_id": args.sample_id,
        "in_tissue_spot_count": int(mask.sum()),
        "domain_count": int(args.n_domains),
        "domain_sizes": {str(key): int(value) for key, value in domains["candidate_domain"].value_counts().sort_index().items()},
        "program_genes_detected": detected,
        "interpretation_limit": "Candidate domains and program scores are not pathologist-validated regions or pure cell-type labels.",
    }
    args.output.mkdir(parents=True, exist_ok=True)
    domains.to_csv(args.output / "spatial_domains.tsv", sep="\t", index=False)
    (args.output / "spatial_domain_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(args.output / "spatial_domain_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
