#!/usr/bin/env python3
"""Spatial gene expression plot."""

import argparse
import os
import time

import numpy as np

from bootstrap import prepare_atlas_paths
from atlas_registry import get_atlas

prepare_atlas_paths()

from io_core import load_gene_sparse, load_n_obs, load_spatial_xy, resolve_gene_name, sample_name, setup_matplotlib, validate_dataset_dir
from spatial_plot_utils import (
    FAST_SPATIAL_DPI,
    auto_point_size,
    create_spatial_axes,
    figsize_for_xy,
    save_spatial_figure,
)


def render_plot(
    xy,
    idx,
    expr,
    gene,
    title,
    out,
    cmap,
    vmin,
    vmax,
    percentile,
    dpi,
    figsize,
    fast,
    axis_labels=("spatial_1", "spatial_2"),
    *,
    show_background=True,
    bg_color="#d4d4d4",
    fixed_canvas=False,
):
    if fast:
        fig, ax, plt = create_spatial_axes(
            fast=True,
            layout="colorbar",
            fixed_canvas=fixed_canvas,
            figsize=figsize,
        )
    else:
        plt = setup_matplotlib()
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        ax.set_facecolor("white")
    n_obs = len(xy)
    n_expr = len(expr)
    x_all, y_all = xy[:, 0], xy[:, 1]
    pt = auto_point_size(n_obs, x=x_all, y=y_all, fast=fast)

    if show_background and n_obs > n_expr:
        expressing = np.zeros(n_obs, dtype=bool)
        expressing[idx] = True
        bg = ~expressing
        ax.scatter(
            x_all[bg], y_all[bg],
            c=bg_color, s=pt, linewidths=0, rasterized=True,
            alpha=0.85, zorder=1,
        )
    elif show_background and n_expr == 0:
        ax.scatter(
            x_all, y_all,
            c=bg_color, s=pt, linewidths=0, rasterized=True,
            alpha=0.85, zorder=1,
        )

    sc = None
    if n_expr > 0:
        sc = ax.scatter(
            x_all[idx], y_all[idx], c=expr, cmap=cmap, s=pt, linewidths=0,
            rasterized=True, vmin=vmin, vmax=vmax, alpha=1.0, zorder=2,
        )

    ax.set_aspect("equal")
    ax.set_xlabel(axis_labels[0])
    ax.set_ylabel(axis_labels[1])
    if fast:
        ax.set_title(f"{gene} expression ({n_expr:,}/{n_obs:,} spots)")
    elif show_background:
        ax.set_title(f"{title} — {gene} expression ({n_expr:,}/{n_obs:,} spots)")
    else:
        ax.set_title(f"{title} — {gene} expression (n={n_expr:,})")

    if sc is not None:
        fig.colorbar(sc, ax=ax, shrink=0.72, pad=0.04, aspect=22).set_label(
            f"{gene} (vmax p{percentile:g})"
        )
    if fast and not fixed_canvas:
        plt.tight_layout()
    elif not fast:
        import matplotlib.pyplot as plt_module
        plt_module.tight_layout()
    save_spatial_figure(fig, out, fast=fast, dpi=dpi, fixed_canvas=fixed_canvas)
    plt.close(fig)


def plot_gene(
    base,
    gene,
    out,
    sample=None,
    fast=False,
    dpi=120,
    cmap="viridis",
    percentile=99.0,
    vmin=None,
    vmax=None,
    use_cache=True,
    timing=False,
    show_background=True,
    fixed_canvas=False,
    *,
    compact=False,
):
    _ = compact  # legacy alias for --compact CLI
    ds = validate_dataset_dir(base)
    if get_atlas().fuzzy_gene_symbols:
        resolved = resolve_gene_name(ds, gene)
        if not resolved:
            raise FileNotFoundError(f"Gene '{gene}' not in dataset var / X/")
        gene = resolved
    title = sample_name(ds, sample)
    out = out or os.path.join(ds.output_dir(), f"spatial_gene_{gene.replace('/', '_')}.png")

    t0 = time.perf_counter()
    xy = load_spatial_xy(ds, use_cache=use_cache)
    idx, expr = load_gene_sparse(ds, gene)
    n_obs = load_n_obs(ds)
    t_load = time.perf_counter() - t0

    if len(expr):
        vmin = vmin if vmin is not None else float(np.min(expr))
        vmax = vmax if vmax is not None else float(np.percentile(expr, percentile))
        if vmax <= vmin:
            vmax = float(np.max(expr))
    else:
        vmin = vmin if vmin is not None else 0.0
        vmax = vmax if vmax is not None else 1.0

    dpi_use = FAST_SPATIAL_DPI if fast else dpi
    x, y = xy[:, 0], xy[:, 1]
    if fast:
        figsize = figsize_for_xy(x, y, fast=True, fixed_canvas=fixed_canvas)
    else:
        figsize = figsize_for_xy(x, y, fast=False)
    t1 = time.perf_counter()
    render_plot(
        xy, idx, expr, gene, title, out, cmap, vmin, vmax, percentile, dpi_use, figsize, fast,
        axis_labels=ds.embedding_axis_labels(),
        show_background=show_background,
        fixed_canvas=fixed_canvas,
    )
    t_plot = time.perf_counter() - t1

    pct = 100 * len(expr) / n_obs
    print(f"{title} / {gene}: {len(expr):,} expressing / {n_obs:,} spots ({pct:.1f}%)")
    print(f"Saved: {out}")
    if timing or (t_load + t_plot) > 2:
        print(f"Timing: load={t_load:.2f}s plot={t_plot:.2f}s")
    return out


def main():
    p = argparse.ArgumentParser(description="Plot spatial gene expression.")
    p.add_argument("data_dir")
    p.add_argument("-g", "--gene", required=True)
    p.add_argument("--sample-name", default=None)
    p.add_argument("-o", "--output", default=None)
    p.add_argument("--dpi", type=int, default=120)
    p.add_argument("--cmap", default="viridis")
    p.add_argument("--vmin", type=float, default=None)
    p.add_argument("--vmax", type=float, default=None)
    p.add_argument("--percentile", type=float, default=99.0)
    p.add_argument("--fast", action="store_true")
    p.add_argument("--no-cache", action="store_true")
    p.add_argument("--timing", action="store_true")
    p.add_argument(
        "--no-background",
        action="store_true",
        help="Do not draw non-expressing spots in gray (legacy style).",
    )
    p.add_argument(
        "--fixed-canvas",
        action="store_true",
        help="Fixed 9×5.5 canvas for side-by-side gallery with cluster maps.",
    )
    p.add_argument(
        "--compact",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    args = p.parse_args()
    plot_gene(
        args.data_dir, args.gene, args.output, args.sample_name,
        fast=args.fast, dpi=args.dpi, cmap=args.cmap,
        percentile=args.percentile, vmin=args.vmin, vmax=args.vmax,
        use_cache=not args.no_cache, timing=args.timing,
        show_background=not args.no_background,
        fixed_canvas=args.fixed_canvas,
        compact=args.compact,
    )


if __name__ == "__main__":
    import sys
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
