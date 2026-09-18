#!/usr/bin/env python3
"""Link Visium spot coordinates to tissue-aware H&E tiles in the same rendered image frame."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spatial-domains", required=True, type=Path)
    parser.add_argument("--he-tiles", required=True, type=Path)
    parser.add_argument("--scalefactors", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--coordinate-frame", choices=["hires", "fullres"], default="hires")
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    spots = pd.read_csv(args.spatial_domains, sep="\t")
    tiles = pd.read_csv(args.he_tiles, sep="\t")
    required_spots = {"sample_id", "barcode", "pxl_col", "pxl_row", "candidate_domain"}
    required_tiles = {"tile_id", "slide_id", "x_px", "y_px", "tile_size_px", "tissue_fraction"}
    if missing := required_spots - set(spots.columns):
        raise SystemExit(f"Spatial domains is missing: {sorted(missing)}")
    if missing := required_tiles - set(tiles.columns):
        raise SystemExit(f"H&E tiles is missing: {sorted(missing)}")
    if (tiles["tile_size_px"] <= 0).any():
        raise SystemExit("tile_size_px must be positive.")

    scale = 1.0
    if args.coordinate_frame == "hires":
        scale = float(json.loads(args.scalefactors.read_text(encoding="utf-8"))["tissue_hires_scalef"])
    spots = spots.copy()
    spots["he_x_px"] = spots["pxl_col"] * scale
    spots["he_y_px"] = spots["pxl_row"] * scale

    linked_rows: list[dict[str, object]] = []
    program_columns = [
        column for column in spots.columns
        if column not in {"sample_id", "barcode", "pxl_col", "pxl_row", "candidate_domain", "he_x_px", "he_y_px"}
    ]
    for spot in spots.itertuples(index=False):
        x, y = float(spot.he_x_px), float(spot.he_y_px)
        matched = tiles.loc[
            (tiles["x_px"] <= x) & (x < tiles["x_px"] + tiles["tile_size_px"])
            & (tiles["y_px"] <= y) & (y < tiles["y_px"] + tiles["tile_size_px"])
        ]
        if matched.empty:
            continue
        tile = matched.iloc[0]
        row = {
            "sample_id": spot.sample_id,
            "barcode": spot.barcode,
            "tile_id": tile.tile_id,
            "slide_id": tile.slide_id,
            "he_x_px": round(x, 4),
            "he_y_px": round(y, 4),
            "candidate_domain": spot.candidate_domain,
            "tile_tissue_fraction": tile.tissue_fraction,
        }
        for column in program_columns:
            row[column] = getattr(spot, column)
        linked_rows.append(row)

    links = pd.DataFrame(linked_rows)
    links_path = args.output / "visium_he_tile_links.tsv"
    if links.empty:
        links = pd.DataFrame(columns=["sample_id", "barcode", "tile_id", "slide_id", "he_x_px", "he_y_px", "candidate_domain", "tile_tissue_fraction", *program_columns])
        summary = pd.DataFrame(columns=["tile_id", "candidate_domain", "spot_count"])
    else:
        summary = links.groupby(["tile_id", "candidate_domain"], as_index=False).size().rename(columns={"size": "spot_count"})
        if program_columns:
            means = links.groupby(["tile_id", "candidate_domain"], as_index=False)[program_columns].mean()
            summary = summary.merge(means, on=["tile_id", "candidate_domain"], how="left")
    links.to_csv(links_path, sep="\t", index=False)
    summary.to_csv(args.output / "he_tile_spatial_evidence.tsv", sep="\t", index=False)

    metadata = {
        "coordinate_frame": args.coordinate_frame,
        "scale_applied": scale,
        "input_spot_count": int(len(spots)),
        "linked_spot_count": int(len(links)),
        "unlinked_spot_count": int(len(spots) - len(links)),
        "interpretation_limit": (
            "A link only means the Visium spot centre falls within a traditional tissue-aware H&E tile. "
            "It does not establish cellular colocalization, pathology diagnosis, or causality."
        ),
    }
    (args.output / "visium_he_link_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(links_path)


if __name__ == "__main__":
    main()
