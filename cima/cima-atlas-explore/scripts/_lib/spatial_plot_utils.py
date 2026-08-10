"""Shared palette / scatter helpers for categorical spatial maps."""

from __future__ import annotations

import colorsys

import numpy as np
from matplotlib.colors import to_rgb

from io_core import setup_matplotlib

# Fixed canvas for --fast PNGs so cluster + gene maps match when shown side-by-side.
FAST_SPATIAL_FIGSIZE = (9.0, 5.5)
FAST_SPATIAL_DPI = 120


def figsize_for_xy(
    x,
    y,
    *,
    fast: bool = False,
    fixed_canvas: bool = False,
    extra_width: float = 0.0,
) -> tuple[float, float]:
    """Figure size from data aspect; fixed canvas only for side-by-side gallery pairs."""
    if fast and fixed_canvas:
        return FAST_SPATIAL_FIGSIZE
    xr = float(np.ptp(x)) or 1.0
    yr = float(np.ptp(y)) or 1.0
    ar = xr / yr
    h = 6.0 if fast else 6.5
    pad = 0.85 if fast else 1.1
    w = h * ar + pad + extra_width
    w_min, w_max = (2.8, 7.0) if fast else (3.6, 8.5)
    h_min, h_max = (4.0, 7.0) if fast else (3.6, 8.5)
    w = float(np.clip(w, w_min, w_max))
    h = float(np.clip(h, h_min, h_max))
    return w, h


def create_spatial_axes(
    *,
    fast: bool,
    dpi: int = 120,
    layout: str = "default",
    fixed_canvas: bool = False,
    figsize: tuple[float, float] | None = None,
):
    """Return (fig, ax, plt). fixed_canvas=True → identical PNG size for gallery pairs."""
    plt = setup_matplotlib()
    if fast and fixed_canvas:
        fig, ax = plt.subplots(figsize=FAST_SPATIAL_FIGSIZE, dpi=FAST_SPATIAL_DPI)
        margins = {
            "default": (0.07, 0.08, 0.84, 0.94),
            "legend": (0.07, 0.08, 0.82, 0.94),
            "colorbar": (0.06, 0.08, 0.84, 0.93),
        }
        left, bottom, right, top = margins.get(layout, margins["default"])
        fig.subplots_adjust(left=left, bottom=bottom, right=right, top=top)
    elif fast:
        fs = figsize or FAST_SPATIAL_FIGSIZE
        fig, ax = plt.subplots(figsize=fs, dpi=FAST_SPATIAL_DPI)
    else:
        fig, ax = plt.subplots(figsize=figsize or (10, 8), dpi=dpi)
    ax.set_facecolor("white")
    return fig, ax, plt


def save_spatial_figure(
    fig,
    out,
    *,
    fast: bool,
    dpi: int = 120,
    fixed_canvas: bool = False,
) -> None:
    """Adaptive fast PNGs use tight bbox; fixed_canvas keeps identical dimensions for galleries."""
    if fast and not fixed_canvas:
        fig.savefig(
            out,
            dpi=FAST_SPATIAL_DPI,
            bbox_inches="tight",
            pad_inches=0.04,
            facecolor="white",
            edgecolor="none",
            transparent=False,
        )
    elif fast:
        fig.savefig(
            out,
            dpi=FAST_SPATIAL_DPI,
            facecolor="white",
            edgecolor="none",
            transparent=False,
        )
    else:
        fig.savefig(out, bbox_inches="tight", pad_inches=0.04, facecolor="white", edgecolor="none")


def auto_point_size(
    n: int,
    *,
    x=None,
    y=None,
    fast: bool = False,
    override: float = 0,
) -> float:
    """Matplotlib scatter ``s`` (points²). Scale up for sparse maps so colors look solid."""
    if override and override > 0:
        return override

    if x is not None and y is not None and len(x) > 1:
        import math

        xr = float(np.ptp(x)) or 1.0
        yr = float(np.ptp(y)) or 1.0
        spacing = math.sqrt((xr * yr) / max(n, 1))
        plot_px = 800.0 if fast else 1000.0
        px_per_unit = plot_px / max(xr, yr)
        diam_pt = 1.15 * spacing * px_per_unit * 72.0 / 120.0
        return float(max(4.0, min(diam_pt ** 2, 500.0)))

    if n <= 5_000:
        return 30.0 if fast else 40.0
    if n <= 25_000:
        return 3.0 if fast else 4.0
    if n <= 100_000:
        return 1.2 if fast else 1.5
    if n <= 500_000:
        return 0.5 if fast else 0.6
    return 0.25 if fast else 0.35


def build_palette(labels, hex_colors):
    plt = setup_matplotlib()
    categories = sorted(set(labels), key=str)
    if hex_colors:
        rgb = []
        for cat in categories:
            c = hex_colors.get(str(cat), hex_colors.get(cat))
            rgb.append(to_rgb(c) if c else None)
        missing = [i for i, r in enumerate(rgb) if r is None]
        if missing:
            cmap = plt.colormaps["tab20"].resampled(max(len(categories), 3))
            for i in missing:
                rgb[i] = cmap(i / max(len(categories) - 1, 1))[:3]
        return categories, np.array(rgb)
    cmap = plt.colormaps["tab20"].resampled(len(categories))
    return categories, np.array([cmap(i / max(len(categories) - 1, 1))[:3] for i in range(len(categories))])


def enhance_palette(palette, *, saturation=1.8, min_lightness=0.32, max_lightness=0.72):
    out = []
    for rgb in palette:
        h, l, s = colorsys.rgb_to_hls(*rgb[:3])
        s = min(1.0, s * saturation)
        l = min(max_lightness, max(min_lightness, l))
        out.append(colorsys.hls_to_rgb(h, l, s))
    return np.array(out)


def scatter_by_category(ax, x, y, labels, categories, palette, point_size):
    from collections import Counter

    cat_to_idx = {c: i for i, c in enumerate(categories)}
    counts = Counter(labels)
    order = sorted(categories, key=lambda c: counts.get(c, 0), reverse=True)
    labels_arr = np.asarray(labels)
    for cat in order:
        mask = labels_arr == cat
        if not np.any(mask):
            continue
        ax.scatter(
            x[mask],
            y[mask],
            c=[palette[cat_to_idx[cat]]],
            s=point_size,
            linewidths=0,
            edgecolors="none",
            rasterized=True,
            alpha=1.0,
        )
