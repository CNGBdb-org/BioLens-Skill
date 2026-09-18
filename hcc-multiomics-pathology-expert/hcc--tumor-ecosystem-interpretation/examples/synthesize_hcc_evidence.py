#!/usr/bin/env python3
"""Create a guarded, structured HCC evidence synthesis from available run artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path | None) -> dict | None:
    return json.loads(path.read_text(encoding="utf-8")) if path and path.exists() else None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spatial-summary", type=Path)
    parser.add_argument("--pathology-qc", type=Path)
    parser.add_argument("--bulk-metadata", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    sources = {
        "spatial": load_json(args.spatial_summary),
        "pathology_qc": load_json(args.pathology_qc),
        "bulk": load_json(args.bulk_metadata),
    }
    available = [name for name, value in sources.items() if value is not None]
    limitations = [
        "This synthesis is research-use only and is not a clinical diagnosis or treatment recommendation.",
        "Malignant hepatocyte claims require at least two independent supports (for example tumor ROI plus CNV, mutation, or a validated tumor label).",
        "Spatial candidate domains/program scores and tissue masks are not pathologist-validated cellular labels.",
    ]
    if not sources["bulk"]:
        limitations.append("No bulk-RNA evidence was supplied; cohort-level expression conclusions are unavailable.")
    if not sources["pathology_qc"]:
        limitations.append("No pathology QC evidence was supplied; image-region evidence is unavailable.")
    if not sources["spatial"]:
        limitations.append("No spatial summary was supplied; spatial-program evidence is unavailable.")
    evidence = {
        "available_modalities": available,
        "spatial": {
            "in_tissue_spot_count": sources["spatial"].get("in_tissue_spot_count"),
            "candidate_domain_count": sources["spatial"].get("domain_count"),
            "detected_programs": sorted(sources["spatial"].get("program_genes_detected", {})),
        } if sources["spatial"] else None,
        "pathology": {
            "image_kind": sources["pathology_qc"].get("image_kind"),
            "tissue_fraction": sources["pathology_qc"].get("tissue_fraction"),
        } if sources["pathology_qc"] else None,
        "bulk": {
            "sample_count": sources["bulk"].get("sample_count"),
            "input_scale": sources["bulk"].get("input_scale"),
            "detected_programs": sorted(sources["bulk"].get("program_genes_detected", {})),
        } if sources["bulk"] else None,
        "limitations": limitations,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
