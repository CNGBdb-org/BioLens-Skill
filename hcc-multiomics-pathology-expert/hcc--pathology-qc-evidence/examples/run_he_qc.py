#!/usr/bin/env python3
"""Run reproducible QC on a rendered H&E image (not a whole-slide reader)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.filters import threshold_otsu


def load_rgb(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"))


def tissue_mask(rgb: np.ndarray) -> tuple[np.ndarray, float]:
    """Return a conservative foreground mask using luminance and colour saturation."""
    scaled = rgb.astype(np.float32) / 255.0
    luminance = 0.2126 * scaled[..., 0] + 0.7152 * scaled[..., 1] + 0.0722 * scaled[..., 2]
    chroma = scaled.max(axis=2) - scaled.min(axis=2)
    try:
        threshold = float(threshold_otsu(luminance))
    except ValueError:
        threshold = 0.9
    # White scanner background is both bright and nearly achromatic.  Keep weakly
    # stained tissue by allowing either a darker pixel or a sufficiently coloured one.
    mask = (luminance < min(threshold + 0.08, 0.95)) | ((chroma > 0.08) & (luminance < 0.98))
    mask = ndimage.binary_opening(mask, structure=np.ones((3, 3)))
    mask = ndimage.binary_closing(mask, structure=np.ones((5, 5)))
    return mask.astype(bool), threshold


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--slide-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    args.output.mkdir(parents=True, exist_ok=True)
    rgb = load_rgb(args.image)
    mask, otsu_threshold = tissue_mask(rgb)
    gray = 0.2126 * rgb[..., 0] + 0.7152 * rgb[..., 1] + 0.0722 * rgb[..., 2]
    laplacian_variance = float(np.var(ndimage.laplace(gray)))

    Image.fromarray((mask * 255).astype(np.uint8), mode="L").save(args.output / "tissue_mask.png")
    thumbnail = Image.fromarray(rgb)
    thumbnail.thumbnail((1024, 1024))
    thumbnail.save(args.output / "thumbnail.png")

    summary = {
        "slide_id": args.slide_id,
        "source_image": str(args.image.resolve()),
        "image_kind": "rendered_he_image",
        "width_px": int(rgb.shape[1]),
        "height_px": int(rgb.shape[0]),
        "tissue_fraction": round(float(mask.mean()), 6),
        "otsu_luminance_threshold": round(otsu_threshold, 6),
        "brightness_mean": round(float(gray.mean()), 4),
        "laplacian_variance": round(laplacian_variance, 4),
        "qc_limit": (
            "Foreground mask is a traditional image-QC estimate, not a tumor/necrosis annotation. "
            "No MPP, magnification, diagnostic grade, or clinical decision is inferred from this rendered image."
        ),
    }
    (args.output / "he_qc_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(args.output / "he_qc_summary.json")


if __name__ == "__main__":
    main()
