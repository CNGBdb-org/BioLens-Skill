#!/usr/bin/env python3
"""Generate a conservative HCC spatial manifest for GEO GSE238264."""

from __future__ import annotations

import argparse
import csv
import tarfile
from pathlib import Path


SAMPLES = {
    "GSM7661255": ("HCC1R", "responder"),
    "GSM7661256": ("HCC2R", "responder"),
    "GSM7661257": ("HCC3R", "responder"),
    "GSM7661258": ("HCC4R", "responder"),
    "GSM7661259": ("HCC5NR", "non_responder"),
    "GSM7661260": ("HCC6NR", "non_responder"),
    "GSM7661261": ("HCC7NR", "non_responder"),
}


def find_archive(input_dir: Path) -> Path:
    archives = sorted(input_dir.glob("GSE238264_RAW.tar"))
    if not archives:
        raise FileNotFoundError("GSE238264_RAW.tar not found")
    return archives[0]


def inspect_samples(archive: Path) -> dict[str, dict[str, bool]]:
    observed = {gsm: {"spatial": False, "histology": False} for gsm in SAMPLES}
    with tarfile.open(archive, "r") as handle:
        for member in handle.getmembers():
            gsm = next((key for key in SAMPLES if key in member.name), None)
            if not gsm or not member.isfile() or not member.name.endswith(".tar.gz"):
                continue
            extracted = handle.extractfile(member)
            if extracted is None:
                continue
            with tarfile.open(fileobj=extracted, mode="r:gz") as nested:
                names = {item.name for item in nested.getmembers() if item.isfile()}
            observed[gsm]["spatial"] = any(name.endswith("filtered_feature_bc_matrix.h5") for name in names)
            observed[gsm]["histology"] = any(name.endswith(("spatial/tissue_hires_image.png", "spatial/tissue_lowres_image.png")) for name in names)
    return observed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    archive = find_archive(args.input_dir)
    observed = inspect_samples(archive)
    missing = {gsm for gsm, components in observed.items() if not components["spatial"]}
    if missing:
        raise SystemExit(f"archive missing expected samples: {sorted(missing)}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fields = ["patient_id", "sample_id", "modality", "disease", "tissue_role", "input_path", "slide_id", "response_group", "pairing_level", "source_accession"]
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t")
        writer.writeheader()
        for gsm, (sample, group) in SAMPLES.items():
            writer.writerow({
                "patient_id": sample,
                "sample_id": gsm,
                "modality": "spatial",
                "disease": "HCC",
                "tissue_role": "tumor",
                "input_path": f"{archive}::{gsm}_{sample}.tar.gz",
                "slide_id": f"{sample}_visium_section",
                "response_group": group,
                "pairing_level": "same_section" if observed[gsm]["histology"] else "",
                "source_accession": "GSE238264",
            })
            if observed[gsm]["histology"]:
                writer.writerow({
                    "patient_id": sample,
                    "sample_id": f"{gsm}_he",
                    "modality": "he",
                    "disease": "HCC",
                    "tissue_role": "tumor",
                    "input_path": f"{archive}::{gsm}_{sample}.tar.gz::spatial/tissue_hires_image.png",
                    "slide_id": f"{sample}_visium_section",
                    "response_group": group,
                    "pairing_level": "same_section",
                    "source_accession": "GSE238264",
                })
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
