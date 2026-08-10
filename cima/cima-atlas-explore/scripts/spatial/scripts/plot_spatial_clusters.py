#!/usr/bin/env python3
"""Spatial map colored by obs category (celltype / annotation)."""

import argparse
import os

import numpy as np

from bootstrap import prepare_atlas_paths
from atlas_registry import DEFAULT_OBS_LABEL, get_atlas

prepare_atlas_paths()

from io_core import load_obs_column, load_spatial_xy, sample_name, schema_colors, setup_matplotlib, validate_dataset_dir
from spatial_plot_utils import (
    auto_point_size,
    build_palette,
    create_spatial_axes,
    enhance_palette,
    figsize_for_xy,
    save_spatial_figure,
    scatter_by_category,
)


def main():
    spec = get_atlas()
    p = argparse.ArgumentParser(description=f"{spec.display_name} spatial plot by obs category.")
    p.add_argument("data_dir")
    p.add_argument("--label", default=DEFAULT_OBS_LABEL)
    p.add_argument("-o", "--output", default=None)
    p.add_argument("--dpi", type=int, default=120)
    p.add_argument("--fast", action="store_true")
    p.add_argument(
        "--fixed-canvas",
        action="store_true",
        help="Fixed 9×5.5 canvas (legacy gallery alignment). Default: adaptive tight crop.",
    )
    p.add_argument("--max-points", type=int, default=0)
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--saturation", type=float, default=1.8)
    p.add_argument("--point-size", type=float, default=0)
    p.add_argument("--no-enhance", action="store_true")
    args = p.parse_args()

    ds = validate_dataset_dir(args.data_dir)
    title = sample_name(ds)
    out = args.output or os.path.join(ds.output_dir(), f"spatial_{args.label}.png")

    xy = load_spatial_xy(ds, use_cache=not args.no_cache)
    labels = load_obs_column(ds, args.label)
    x, y = xy[:, 0], xy[:, 1]
    n = len(x)
    print(f"{title} / {args.label}: {n:,} spots, {len(set(labels))} categories")

    categories, palette = build_palette(labels, schema_colors(ds, args.label))
    if not args.no_enhance and args.saturation != 1.0:
        palette = enhance_palette(palette, saturation=args.saturation)

    labels_plot = np.asarray(labels)
    if args.max_points > 0 and n > args.max_points:
        rng = np.random.default_rng(42)
        sel = rng.choice(n, args.max_points, replace=False)
        x, y, labels_plot = x[sel], y[sel], labels_plot[sel]
        print(f"  subsampled to {len(x):,}")

    dpi = 120 if args.fast else args.dpi
    fixed = args.fast and args.fixed_canvas
    if args.fast:
        extra = min(2.8, 0.55 + len(categories) * 0.032)
        figsize = figsize_for_xy(x, y, fast=True, fixed_canvas=fixed, extra_width=extra)
        layout = "legend" if fixed else "default"
        fig, ax, plt = create_spatial_axes(fast=True, layout=layout, fixed_canvas=fixed, figsize=figsize)
    else:
        plt = setup_matplotlib()
        fig, ax = plt.subplots(figsize=(10, 8), dpi=dpi)
        ax.set_facecolor("white")
    point_size = auto_point_size(n, x=x, y=y, fast=args.fast, override=args.point_size)
    scatter_by_category(ax, x, y, labels_plot, categories, palette, point_size)
    ax.set_aspect("equal")
    axis_labels = ds.embedding_axis_labels() if hasattr(ds, "embedding_axis_labels") else ("spatial_1", "spatial_2")
    ax.set_xlabel(axis_labels[0])
    ax.set_ylabel(axis_labels[1])
    ax.set_title(f"{title} — {args.label} (n={n:,})")
    handles = [
        plt.Line2D([0], [0], marker="o", color="w", markerfacecolor=palette[i], markersize=5, label=str(c))
        for i, c in enumerate(categories)
    ]
    ncol = 1 if args.fast else (2 if len(categories) > 12 else 1)
    ax.legend(
        handles=handles,
        title=args.label,
        bbox_to_anchor=(1.0, 1.0),
        loc="upper left",
        fontsize=5 if args.fast else 6,
        markerscale=1.6 if args.fast else 2,
        ncol=ncol,
        frameon=False,
        borderaxespad=0.0,
        labelspacing=0.35 if args.fast else 0.5,
    )
    if not args.fast:
        plt.tight_layout()
    elif not fixed:
        fig.tight_layout()
    save_spatial_figure(fig, out, fast=args.fast, dpi=dpi, fixed_canvas=fixed)
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
