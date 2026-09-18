#!/usr/bin/env python3
"""Create tissue-aware H&E tile coordinates and optional PNG patches."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--mask", required=True, type=Path, help="Mask produced by run_he_qc.py")
    parser.add_argument("--slide-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--tile-size", type=int, default=512)
    parser.add_argument("--stride", type=int, default=512)
    parser.add_argument("--min-tissue-fraction", type=float, default=0.5)
    parser.add_argument("--max-tiles", type=int, default=1000)
    parser.add_argument("--write-patches", action="store_true")
    args = parser.parse_args()

    if args.tile_size <= 0 or args.stride <= 0 or not 0 <= args.min_tissue_fraction <= 1:
        sys.exit("tile-size/stride must be positive and min-tissue-fraction must be in [0, 1].")
    args.output.mkdir(parents=True, exist_ok=True)
    patches_dir = args.output / "patches"
    if args.write_patches:
        patches_dir.mkdir(exist_ok=True)

    with Image.open(args.image) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        with Image.open(args.mask) as mask_image:
            mask = np.asarray(mask_image.convert("L")) > 0
        if mask.shape != (height, width):
            sys.exit("Mask dimensions must match image dimensions exactly.")

        rows: list[dict[str, object]] = []
        for y in range(0, max(1, height - args.tile_size + 1), args.stride):
            for x in range(0, max(1, width - args.tile_size + 1), args.stride):
                if x + args.tile_size > width or y + args.tile_size > height:
                    continue
                fraction = float(mask[y : y + args.tile_size, x : x + args.tile_size].mean())
                if fraction < args.min_tissue_fraction:
                    continue
                tile_id = f"{args.slide_id}_x{x}_y{y}_s{args.tile_size}"
                patch_path = ""
                if args.write_patches:
                    patch_path = str((patches_dir / f"{tile_id}.png").resolve())
                    rgb.crop((x, y, x + args.tile_size, y + args.tile_size)).save(patch_path)
                rows.append({
                    "tile_id": tile_id,
                    "slide_id": args.slide_id,
                    "x_px": x,
                    "y_px": y,
                    "tile_size_px": args.tile_size,
                    "tissue_fraction": round(fraction, 6),
                    "patch_path": patch_path,
                    "selection_reason": "traditional_tissue_mask",
                })
                if len(rows) >= args.max_tiles:
                    break
            if len(rows) >= args.max_tiles:
                break

    output_tsv = args.output / "he_tile_coordinates.tsv"
    columns = ["tile_id", "slide_id", "x_px", "y_px", "tile_size_px", "tissue_fraction", "patch_path", "selection_reason"]
    with output_tsv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)
    print(output_tsv)


if __name__ == "__main__":
    main()
