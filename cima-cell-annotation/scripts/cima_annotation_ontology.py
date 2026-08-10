#!/usr/bin/env python3
"""CIMA L1–L4 marker-signature ontology helpers.

Ontology sourced from TrueBlood CellType marker table / hierarchy:
https://db.cngb.org/trueblood/cima/cellType
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ONTOLOGY_PATH = Path(__file__).resolve().parent / "cima_celltype_ontology.json"

# Step-1 coarse labels (celltype_1st) → CIMA L1 lineage names
CELLTYPE_1ST_TO_L1 = {
    "Naive B": "B cells",
    "Naive B cell": "B cells",
    "Memory B": "B cells",
    "Memory B cell": "B cells",
    "Plasma&Cycling T": "B cells",
    "Plasma": "B cells",
    "Plasma cell": "B cells",
    "B cells": "B cells",
    "B": "B cells",
    "T cells": "other T",
    "CD4 T": "CD4 T",
    "Naive CD4 T cell": "CD4 T",
    "Memory CD4 T cell": "CD4 T",
    "Treg cell": "CD4 T",
    "CD8 T": "CD8 T",
    "Naive CD8 T cell": "CD8 T",
    "GZMB CD8 T cell": "CD8 T",
    "GZMK CD8 T cell": "CD8 T",
    "NK cells": "NK",
    "NK": "NK",
    "CD16 NK cell": "NK",
    "CD56 NK cell": "NK",
    "ILC": "ILC",
    "pDC": "Myeloid",
    "cDC": "Myeloid",
    "Dendritic cell": "Myeloid",
    "cMono": "Myeloid",
    "ncMono": "Myeloid",
    "CD14 monocyte": "Myeloid",
    "CD16 monocyte": "Myeloid",
    "Mono": "Myeloid",
    "Myeloid": "Myeloid",
    "Megakaryocyte": "Myeloid",
    "HSPC": "HSPC",
    "Erythrocyte": "HSPC",
    "Red blood cell": "HSPC",
}

LINEAGE_FILTER = {
    "B_cells": ["B cells"],
    "myeloid": ["Myeloid", "HSPC"],
    "TNK": ["CD4 T", "CD8 T", "NK", "ILC", "other T"],
    "CD4T": ["CD4 T"],
    "CD8T": ["CD8 T"],
    "NK": ["NK", "ILC"],
}


@lru_cache(maxsize=1)
def load_ontology(path: str | None = None) -> dict:
    p = Path(path) if path else ONTOLOGY_PATH
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def parse_marker_string(marker: str) -> tuple[list[str], list[str]]:
    """Parse 'CD3D+,CD4+,CD8A-,HLA-DPB1+' into (positive, negative) gene lists."""
    pos, neg = [], []
    if not marker:
        return pos, neg
    for tok in marker.split(","):
        tok = tok.strip()
        if not tok:
            continue
        # Trailing sense: +, -, −, or low. Gene body may contain hyphens (HLA-DPB1).
        m = re.match(r"^(.+?)(\+|−|-|low)$", tok)
        if m:
            gene, sense = m.group(1).strip(), m.group(2)
        else:
            gene, sense = tok, "+"
        if not gene:
            continue
        if sense == "+":
            pos.append(gene)
        else:
            neg.append(gene)

    def uniq(xs):
        seen = set()
        out = []
        for x in xs:
            if x not in seen:
                seen.add(x)
                out.append(x)
        return out

    return uniq(pos), uniq(neg)


def nodes_by_level(onto: dict | None = None) -> dict[int, list[dict]]:
    onto = onto or load_ontology()
    out: dict[int, list[dict]] = {1: [], 2: [], 3: [], 4: []}
    for n in onto["nodes"]:
        out.setdefault(n["level"], []).append(n)
    return out


def leaves_under_l1(l1: str, onto: dict | None = None) -> list[dict]:
    onto = onto or load_ontology()
    return [
        n
        for n in onto["nodes"]
        if n.get("is_leaf") and n.get("cell_type_l1") == l1
    ]


def all_leaves(onto: dict | None = None) -> list[dict]:
    onto = onto or load_ontology()
    return [n for n in onto["nodes"] if n.get("is_leaf")]


def map_celltype_1st_to_l1(labels: pd.Series) -> pd.Series:
    def one(x: str) -> str:
        if x in CELLTYPE_1ST_TO_L1:
            return CELLTYPE_1ST_TO_L1[x]
        xl = x.lower()
        if "b cell" in xl or xl.startswith("bn") or "plasma" in xl:
            return "B cells"
        if "cd4" in xl or "treg" in xl:
            return "CD4 T"
        if "cd8" in xl:
            return "CD8 T"
        if "nk" in xl:
            return "NK"
        if "mono" in xl or "dc" in xl or "myeloid" in xl or "megakary" in xl:
            return "Myeloid"
        if "hspc" in xl or "eryth" in xl or "red blood" in xl:
            return "HSPC"
        if "t cell" in xl or xl == "t cells":
            return "other T"
        return x

    return labels.astype(str).map(one)


def _gene_vector(adata, genes: list[str]) -> np.ndarray | None:
    present = [g for g in genes if g in adata.var_names]
    if not present:
        return None
    X = adata[:, present].X
    if hasattr(X, "toarray"):
        X = X.toarray()
    return np.asarray(X, dtype=np.float64)


def score_signature(adata, positive: list[str], negative: list[str]) -> np.ndarray:
    """Per-cell signature: mean(pos) - mean(neg); missing gene sets → 0."""
    n = adata.n_obs
    pos_m = _gene_vector(adata, positive)
    neg_m = _gene_vector(adata, negative)
    score = np.zeros(n, dtype=np.float64)
    if pos_m is not None:
        score += pos_m.mean(axis=1)
    if neg_m is not None:
        score -= neg_m.mean(axis=1)
    return score


def score_nodes(adata, nodes: list[dict]) -> pd.DataFrame:
    """Return DataFrame (cells × node names) of signature scores."""
    cols = {}
    for node in nodes:
        pos, neg = parse_marker_string(node.get("marker") or "")
        cols[node["name"]] = score_signature(adata, pos, neg)
    if not cols:
        return pd.DataFrame(index=adata.obs_names)
    return pd.DataFrame(cols, index=adata.obs_names)


def assign_l1(adata, onto: dict | None = None, prefer_existing: str | None = "celltype_1st") -> pd.Series:
    """Assign L1 labels: prefer mapped celltype_1st, else score L1 signatures."""
    onto = onto or load_ontology()
    l1_nodes = [n for n in onto["nodes"] if n["level"] == 1]
    known = {n["name"] for n in l1_nodes}
    scores = score_nodes(adata, l1_nodes)
    best = scores.idxmax(axis=1)

    if prefer_existing and prefer_existing in adata.obs.columns:
        mapped = map_celltype_1st_to_l1(adata.obs[prefer_existing]).astype(str)
        # Refine ambiguous / unknown with marker scores
        need = mapped.isin(["other T", "T cells"]) | ~mapped.isin(known)
        mapped = mapped.copy()
        mapped.loc[need] = best.loc[need]
        return mapped.astype(str)

    return best.astype(str)


def assign_hierarchical(
    adata,
    cluster_key: str,
    l1_key: str = "cell_type_l1",
    onto: dict | None = None,
    min_margin: float = 0.0,
) -> pd.DataFrame:
    """Assign L2–L4 from marker scores aggregated by Leiden cluster within each L1.

    Returns DataFrame with columns:
      cell_type_l1, cell_type_l2, cell_type_l3, cell_type_l4,
      annotation_score, annotation_margin, annotation_leaf
    """
    onto = onto or load_ontology()
    node_by_name = {n["name"]: n for n in onto["nodes"]}

    out = pd.DataFrame(index=adata.obs_names)
    out["cell_type_l1"] = adata.obs[l1_key].astype(str)
    out["cell_type_l2"] = pd.NA
    out["cell_type_l3"] = pd.NA
    out["cell_type_l4"] = pd.NA
    out["annotation_leaf"] = pd.NA
    out["annotation_score"] = np.nan
    out["annotation_margin"] = np.nan

    for l1, idx in out.groupby("cell_type_l1", observed=False).groups.items():
        idx = list(idx)
        if not idx:
            continue
        sub = adata[idx]
        candidates = leaves_under_l1(str(l1), onto)
        if not candidates:
            # fall back to L1 itself
            out.loc[idx, "cell_type_l4"] = l1
            out.loc[idx, "annotation_leaf"] = l1
            continue

        scores = score_nodes(sub, candidates)
        # cluster-level mean scores
        clusters = sub.obs[cluster_key].astype(str)
        for cl, cl_idx in clusters.groupby(clusters, observed=False).groups.items():
            cl_idx = list(cl_idx)
            mean_scores = scores.loc[cl_idx].mean(axis=0)
            order = mean_scores.sort_values(ascending=False)
            best_name = str(order.index[0])
            best_score = float(order.iloc[0])
            second = float(order.iloc[1]) if len(order) > 1 else -np.inf
            margin = best_score - second
            if margin < min_margin:
                # keep best anyway but flag low margin
                pass
            node = node_by_name[best_name]
            path = node.get("path") or [best_name]
            out.loc[cl_idx, "cell_type_l1"] = path[0] if path else l1
            out.loc[cl_idx, "cell_type_l2"] = path[1] if len(path) > 1 else pd.NA
            out.loc[cl_idx, "cell_type_l3"] = path[2] if len(path) > 2 else pd.NA
            out.loc[cl_idx, "cell_type_l4"] = node.get("cell_type_l4") or best_name
            out.loc[cl_idx, "annotation_leaf"] = best_name
            out.loc[cl_idx, "annotation_score"] = best_score
            out.loc[cl_idx, "annotation_margin"] = margin

    return out


def annotate_adata(
    adata,
    cluster_key: str,
    onto: dict | None = None,
    prefer_l1_from: str | None = "celltype_1st",
    min_margin: float = 0.0,
):
    """In-place write cell_type_l1..l4 (+ score columns)."""
    onto = onto or load_ontology()
    adata.obs["cell_type_l1"] = assign_l1(adata, onto=onto, prefer_existing=prefer_l1_from).values
    assigned = assign_hierarchical(
        adata,
        cluster_key=cluster_key,
        l1_key="cell_type_l1",
        onto=onto,
        min_margin=min_margin,
    )
    for col in assigned.columns:
        adata.obs[col] = assigned[col].values
    return adata
