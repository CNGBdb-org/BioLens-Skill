#!/usr/bin/env python3
"""Helpers for multi-round CIMA cell-annotation refinement."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def parse_cluster_list(text: str | None) -> list[str]:
    """Parse '0,2,5' or '0 2 5' into cluster id strings."""
    if not text:
        return []
    parts = [p.strip() for p in text.replace(";", ",").replace(" ", ",").split(",")]
    return [p for p in parts if p]


def parse_relabel_map(spec: str | None) -> dict[str, str]:
    """Parse '2:Doublet,5:Unknown' or a CSV path with columns cluster,label."""
    if not spec:
        return {}
    path = Path(spec)
    if path.is_file():
        sep = "\t" if path.suffix.lower() in {".tsv", ".txt"} else ","
        df = pd.read_csv(path, sep=sep)
        cols = {c.lower(): c for c in df.columns}
        c_col = cols.get("cluster") or cols.get("leiden") or list(df.columns)[0]
        l_col = cols.get("label") or cols.get("cell_type_l4") or cols.get("annotation") or list(df.columns)[1]
        return {str(r[c_col]).strip(): str(r[l_col]).strip() for _, r in df.iterrows()}

    out: dict[str, str] = {}
    for tok in spec.replace(";", ",").split(","):
        tok = tok.strip()
        if not tok:
            continue
        if ":" not in tok and "=" not in tok:
            raise ValueError(f"Bad relabel token {tok!r}; use cluster:label")
        sep = ":" if ":" in tok else "="
        cl, lab = tok.split(sep, 1)
        out[cl.strip()] = lab.strip()
    return out


def find_cluster_key(adata, preferred: str | None = None, resolution: float | None = None) -> str:
    if preferred and preferred in adata.obs.columns:
        return preferred
    if resolution is not None:
        cand = f"leiden_r{resolution}"
        if cand in adata.obs.columns:
            return cand
    leiden_cols = [c for c in adata.obs.columns if str(c).startswith("leiden")]
    if not leiden_cols:
        raise ValueError(
            "No leiden/* cluster column found. Pass --cluster-key or run a first annotation round."
        )
    # Prefer columns that look like leiden_r<float>
    scored = sorted(leiden_cols, key=lambda c: (0 if "leiden_r" in c else 1, c))
    return scored[0]


def export_ambiguous_clusters(
    obs: pd.DataFrame,
    *,
    cluster_key: str,
    out_path: str | Path,
    margin_thresh: float,
    label_col: str = "cell_type_l4",
) -> pd.DataFrame:
    """Write per-cluster margin summary; flag ambiguous when median margin < thresh."""
    if cluster_key not in obs.columns:
        raise ValueError(f"cluster_key {cluster_key!r} missing from obs")
    if "annotation_margin" not in obs.columns:
        raise ValueError("annotation_margin missing; run signature annotation first")

    label_col = label_col if label_col in obs.columns else (
        "custom_label" if "custom_label" in obs.columns else "annotation_leaf"
    )

    rows = []
    for cl, idx in obs.groupby(obs[cluster_key].astype(str), observed=False).groups.items():
        sub = obs.loc[list(idx)]
        margins = pd.to_numeric(sub["annotation_margin"], errors="coerce")
        labels = sub[label_col].astype(str) if label_col in sub.columns else pd.Series(["NA"] * len(sub))
        vc = labels.value_counts()
        top = str(vc.index[0]) if len(vc) else "NA"
        top_frac = float(vc.iloc[0] / len(sub)) if len(vc) else np.nan
        med = float(margins.median()) if margins.notna().any() else np.nan
        rows.append(
            {
                "cluster": cl,
                "n_cells": int(len(sub)),
                "median_margin": med,
                "mean_margin": float(margins.mean()) if margins.notna().any() else np.nan,
                "min_margin": float(margins.min()) if margins.notna().any() else np.nan,
                "top_label": top,
                "top_label_frac": top_frac,
                "ambiguous": bool(med < margin_thresh) if margins.notna().any() else True,
            }
        )
    summary = pd.DataFrame(rows).sort_values(["ambiguous", "median_margin"], ascending=[False, True])
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_path, index=False)
    return summary


def apply_forced_labels(
    adata,
    *,
    cluster_key: str,
    relabel: dict[str, str],
    label_cols: tuple[str, ...] = (
        "cell_type_l4",
        "cell_type_l3",
        "cell_type_l2",
        "annotation_leaf",
        "custom_label",
    ),
) -> int:
    """Force-write labels for clusters in *relabel*. Returns n cells changed."""
    if not relabel:
        return 0
    cl = adata.obs[cluster_key].astype(str)
    n = 0
    for cluster, label in relabel.items():
        mask = cl == str(cluster)
        n_hit = int(mask.sum())
        if n_hit == 0:
            continue
        n += n_hit
        for col in label_cols:
            if col not in adata.obs.columns and col not in ("cell_type_l4", "annotation_leaf"):
                continue
            if col not in adata.obs.columns:
                adata.obs[col] = ""
            # Categorical cannot accept new categories in-place
            if pd.api.types.is_categorical_dtype(adata.obs[col]):
                adata.obs[col] = adata.obs[col].astype(object)
            adata.obs.loc[mask, col] = label
        if "annotation_margin" in adata.obs.columns:
            adata.obs.loc[mask, "annotation_margin"] = np.nan
        if "annotation_score" in adata.obs.columns:
            adata.obs.loc[mask, "annotation_score"] = np.nan
    return n
