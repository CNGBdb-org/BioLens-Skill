#!/usr/bin/env python3
"""Create a conservative HCC sample-manifest draft by scanning local files."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff"}
WSI_EXTENSIONS = {".svs", ".ndpi", ".mrxs", ".scn"}


def classify(path: Path) -> str | None:
    name = path.name.lower()
    if path.suffix.lower() == ".h5ad":
        return "scrna"
    if name.endswith("filtered_feature_bc_matrix.h5") or name.endswith("raw_feature_bc_matrix.h5"):
        return "spatial" if (path.parent / "spatial").exists() else "unknown_10x_h5"
    if path.suffix.lower() in WSI_EXTENSIONS:
        return "pathology"
    if path.suffix.lower() in IMAGE_EXTENSIONS and any(token in name for token in ("tissue_hires", "h&e", "h_e", "_he.", "he_", "histology")):
        return "he"
    if path.suffix.lower() in {".csv", ".tsv", ".txt"} and any(token in name for token in ("count", "expression", "tpm", "fpkm")):
        return "bulk_rna"
    return None


def sample_id_for(path: Path, modality: str) -> str:
    if modality in {"spatial", "unknown_10x_h5"}:
        return path.parent.name
    if modality == "he" and path.parent.name.lower() == "spatial":
        return path.parent.parent.name
    return path.stem


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Data file or directory to scan")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--disease", default="HCC", help="Use unknown if HCC scope has not been confirmed")
    args = parser.parse_args()
    if not args.input.exists():
        raise SystemExit(f"Input does not exist: {args.input}")
    paths = [args.input] if args.input.is_file() else sorted(path for path in args.input.rglob("*") if path.is_file())

    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for path in paths:
        modality = classify(path)
        if modality is None:
            continue
        key = (modality, str(path.resolve()))
        if key in seen:
            continue
        seen.add(key)
        rows.append({
            "patient_id": "unknown",
            "sample_id": sample_id_for(path, modality),
            "modality": modality,
            "disease": args.disease,
            "tissue_role": "unknown",
            "input_path": str(path.resolve()),
            "pairing_level": "unknown",
            "needs_confirmation": "patient_id,tissue_role,pairing_level",
        })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    columns = ["patient_id", "sample_id", "modality", "disease", "tissue_role", "input_path", "pairing_level", "needs_confirmation"]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} draft rows: {args.output}")
    print("All patient, tissue-role, and pairing fields remain unknown until confirmed.")


if __name__ == "__main__":
    main()
