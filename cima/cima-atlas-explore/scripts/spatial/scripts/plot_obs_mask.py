#!/usr/bin/env python3
"""Highlight obs group(s); other spots gray."""

import argparse
import sys

import numpy as np
from matplotlib.colors import to_rgb

from bootstrap import prepare_atlas_paths
from atlas_registry import DEFAULT_OBS_LABEL

prepare_atlas_paths()

from io_core import load_obs_column, load_spatial_xy, sample_name, schema_colors, setup_matplotlib, validate_dataset_dir
from spatial_plot_utils import auto_point_size


def _parse_highlight(values):
    out = []
    for v in values:
        for part in str(v).split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out


def main():
    p = argparse.ArgumentParser(description="Highlight obs label(s) on spatial map.")
    p.add_argument("data_dir")
    p.add_argument("--highlight", action="append", help="Label to highlight (repeatable)")
    p.add_argument("--celltype", "-c", action="append", help="Alias for --highlight (HESTA)")
    p.add_argument("--label", "-l", action="append", help="Alias for --highlight")
    p.add_argument("--by", default=DEFAULT_OBS_LABEL)
    p.add_argument("-o", "--output", default=None)
    p.add_argument("--dpi", type=int, default=120)
    p.add_argument("--fast", action="store_true")
    p.add_argument("--no-cache", action="store_true")
    args = p.parse_args()

    raw = (args.highlight or []) + (args.celltype or []) + (args.label or [])
    if not raw:
        p.error("Provide --highlight, -c/--celltype, or -l/--label")
    labels_hi = _parse_highlight(raw)

    ds = validate_dataset_dir(args.data_dir)
    title = sample_name(ds)
    safe = "_".join(x.replace("/", "_").replace(" ", "_") for x in labels_hi)
    out = args.output or os.path.join(ds.output_dir(), f"spatial_mask_{safe}.png")

    xy = load_spatial_xy(ds, use_cache=not args.no_cache)
    obs = load_obs_column(ds, args.by)
    x, y = xy[:, 0], xy[:, 1]
    hex_colors = schema_colors(ds, args.by)

    colors = np.array([[0.85, 0.85, 0.85]] * len(obs))
    highlight_mask = np.zeros(len(obs), dtype=bool)
    stats = []

    for lab in labels_hi:
        mask = obs == lab
        n_hit = int(mask.sum())
        if n_hit == 0:
            avail = sorted(set(obs), key=str)[:20]
            raise ValueError(f"Label '{lab}' not found. Examples: {', '.join(str(a) for a in avail)}")
        rgb = to_rgb(hex_colors.get(lab, hex_colors.get(str(lab), "#E64B35")))
        colors[mask] = rgb
        highlight_mask |= mask
        stats.append((lab, n_hit))

    n = len(x)
    bg_size = auto_point_size(n, x=x, y=y, fast=args.fast)
    hi_size = bg_size * 1.4
    plt = setup_matplotlib()
    dpi = 120 if args.fast else args.dpi
    fig, ax = plt.subplots(figsize=(9, 7) if args.fast else (10, 8), dpi=dpi)
    ax.scatter(x, y, c=colors, s=bg_size, linewidths=0, rasterized=True, alpha=1.0)
    ax.scatter(x[highlight_mask], y[highlight_mask], c=colors[highlight_mask], s=hi_size, linewidths=0, rasterized=True, alpha=1.0)
    ax.set_aspect("equal")
    ax.set_title(f"{title} — {' / '.join(labels_hi)} (n={highlight_mask.sum():,} / {len(x):,} spots)")
    import matplotlib.pyplot as plt_module
    plt_module.tight_layout()
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    for lab, n_hit in stats:
        print(f"{title} / {lab}: {n_hit:,} spots ({100 * n_hit / len(x):.1f}%)")
    print(f"Saved: {out}")


if __name__ == "__main__":
    import os
    try:
        main()
    except (FileNotFoundError, ValueError) as e:
        print(e, file=sys.stderr)
        sys.exit(1)
