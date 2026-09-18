#!/usr/bin/env python3
"""Score transparent, small HCC-relevant gene programs from a bulk RNA matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROGRAMS = {
    "hepatocyte_differentiation": ["ALB", "APOA1", "CPS1", "HNF4A", "TAT"],
    "epithelial_tumor_candidate": ["AFP", "GPC3", "EPCAM", "KRT8", "KRT18", "KRT19"],
    "immune": ["PTPRC", "CD3D", "TRBC2", "NKG7", "LST1"],
    "myeloid": ["LYZ", "C1QA", "C1QB", "APOE", "FCER1G"],
    "fibroblast_ecm": ["COL1A1", "COL1A2", "COL3A1", "DCN", "LUM"],
    "endothelial": ["KDR", "EMCN", "PECAM1", "VWF", "ENG"],
    "hypoxia_glycolysis": ["CA9", "VEGFA", "SLC2A1", "LDHA", "ENO1"],
}


def normalize(matrix: pd.DataFrame, input_scale: str) -> pd.DataFrame:
    if input_scale == "counts":
        library_sizes = matrix.sum(axis=0)
        if (library_sizes <= 0).any():
            raise SystemExit("All samples must have positive library size for counts normalization.")
        return np.log1p(matrix.divide(library_sizes, axis=1) * 10_000.0)
    if input_scale == "normalized":
        return matrix
    raise AssertionError(input_scale)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expression", required=True, type=Path, help="TSV: first column gene, remaining columns samples")
    parser.add_argument("--input-scale", choices=["counts", "normalized"], required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    raw = pd.read_csv(args.expression, sep="\t")
    if raw.shape[1] < 2:
        raise SystemExit("Expression TSV needs a gene column and at least one sample column.")
    gene_column = raw.columns[0]
    genes = raw[gene_column].astype(str).str.upper()
    if genes.duplicated().any():
        raise SystemExit("Gene identifiers must be unique after uppercasing.")
    expression = raw.drop(columns=[gene_column]).apply(pd.to_numeric, errors="raise")
    if (expression < 0).any().any():
        raise SystemExit("Expression values cannot be negative.")
    expression.index = genes
    normalized = normalize(expression, args.input_scale)

    scores = pd.DataFrame(index=normalized.columns)
    detected: dict[str, list[str]] = {}
    for program, program_genes in PROGRAMS.items():
        available = [gene for gene in program_genes if gene in normalized.index]
        detected[program] = available
        scores[program] = normalized.loc[available].mean(axis=0) if available else np.nan
    scores.index.name = "sample_id"
    args.output.mkdir(parents=True, exist_ok=True)
    scores.reset_index().to_csv(args.output / "bulk_hcc_program_scores.tsv", sep="\t", index=False)
    metadata = {
        "input_scale": args.input_scale,
        "normalization": "log1p(CP10K)" if args.input_scale == "counts" else "as supplied",
        "sample_count": int(expression.shape[1]),
        "gene_count": int(expression.shape[0]),
        "program_genes_detected": detected,
        "interpretation_limit": (
            "Program scores are expression summaries, not inferred cell fractions, tumor purity, prognosis, "
            "or treatment-response predictions. Assess cohort design and confounders before group comparison."
        ),
    }
    (args.output / "bulk_hcc_program_score_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(args.output / "bulk_hcc_program_scores.tsv")


if __name__ == "__main__":
    main()
