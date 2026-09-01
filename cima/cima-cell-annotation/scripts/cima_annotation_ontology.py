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
    force_l1: str | None = None,
):
    """In-place write cell_type_l1..l4 (+ score columns).

    force_l1: if set (e.g. \"Custom\"), skip L1 scoring and assign every cell that label.
    """
    onto = onto or load_ontology()
    if force_l1:
        adata.obs["cell_type_l1"] = str(force_l1)
    else:
        adata.obs["cell_type_l1"] = assign_l1(
            adata, onto=onto, prefer_existing=prefer_l1_from
        ).values
    assigned = assign_hierarchical(
        adata,
        cluster_key=cluster_key,
        l1_key="cell_type_l1",
        onto=onto,
        min_margin=min_margin,
    )
    for col in assigned.columns:
        adata.obs[col] = assigned[col].values
    # Mirror leaf into custom_label when ontology came from a user marker table
    if onto.get("source_kind") in {"custom_marker_table", "merged_marker_table"}:
        adata.obs["custom_label"] = assigned["annotation_leaf"].astype(str).values
    return adata


# ---------------------------------------------------------------------------
# Custom / merge marker tables
# ---------------------------------------------------------------------------

_LABEL_COLS = ("label", "celltype", "cell_type", "name", "annotation")
_MARKER_COLS = ("markers", "marker", "signature")
_POS_COLS = ("positive", "pos", "markers_pos")
_NEG_COLS = ("negative", "neg", "markers_neg")
_L1_COLS = ("cell_type_l1", "l1", "lineage", "lineage_l1")


def _pick_col(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    lower = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand in lower:
            return lower[cand]
    return None


def _genes_to_marker_string(positive: list[str], negative: list[str]) -> str:
    parts = [f"{g}+" for g in positive] + [f"{g}-" for g in negative]
    return ",".join(parts)


def load_marker_table(path: str | Path) -> pd.DataFrame:
    """Load a user marker table (csv/tsv).

    Accepted columns (case-insensitive):
      - label | celltype | name  (required)
      - markers | marker         (TrueBlood-style: GENE+,GENE-)
      - OR positive / negative   (comma/semicolon/space separated gene lists)
      - cell_type_l1 | l1        (optional; required for merge of *new* labels)
    """
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Marker table not found: {path}")
    sep = "\t" if path.suffix.lower() in {".tsv", ".txt"} else ","
    df = pd.read_csv(path, sep=sep)
    if df.empty:
        raise ValueError(f"Marker table is empty: {path}")

    label_col = _pick_col(list(df.columns), _LABEL_COLS)
    if not label_col:
        raise ValueError(
            f"Marker table needs a label column ({'/'.join(_LABEL_COLS)}). Got: {list(df.columns)}"
        )
    marker_col = _pick_col(list(df.columns), _MARKER_COLS)
    pos_col = _pick_col(list(df.columns), _POS_COLS)
    neg_col = _pick_col(list(df.columns), _NEG_COLS)
    l1_col = _pick_col(list(df.columns), _L1_COLS)

    if not marker_col and not pos_col:
        raise ValueError(
            "Marker table needs 'markers' (GENE+,GENE-) or 'positive'[/negative] columns."
        )

    rows = []
    for _, r in df.iterrows():
        label = str(r[label_col]).strip()
        if not label or label.lower() == "nan":
            continue
        if marker_col and pd.notna(r.get(marker_col)) and str(r[marker_col]).strip():
            marker = str(r[marker_col]).strip()
            pos, neg = parse_marker_string(marker)
        else:
            def _split_genes(val) -> list[str]:
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    return []
                text = str(val).strip()
                if not text or text.lower() == "nan":
                    return []
                parts = re.split(r"[,;|\s]+", text)
                return [p.strip() for p in parts if p.strip()]

            pos = _split_genes(r[pos_col]) if pos_col else []
            neg = _split_genes(r[neg_col]) if neg_col else []
            marker = _genes_to_marker_string(pos, neg)
        if not pos and not neg:
            raise ValueError(f"Row '{label}' has no usable markers.")
        l1 = None
        if l1_col and pd.notna(r.get(l1_col)) and str(r[l1_col]).strip():
            l1 = str(r[l1_col]).strip()
        rows.append(
            {
                "label": label,
                "marker": marker,
                "positive": pos,
                "negative": neg,
                "cell_type_l1": l1,
            }
        )
    if not rows:
        raise ValueError(f"No valid marker rows in {path}")
    return pd.DataFrame(rows)


def ontology_from_marker_table(
    table: pd.DataFrame,
    *,
    default_l1: str = "Custom",
    source_path: str | None = None,
) -> dict:
    """Build a minimal ontology: each row is a leaf under its L1 (or default_l1)."""
    l1_names: list[str] = []
    for v in table["cell_type_l1"].tolist():
        name = v if isinstance(v, str) and v else default_l1
        if name not in l1_names:
            l1_names.append(name)

    nodes: list[dict] = []
    for l1 in l1_names:
        nodes.append(
            {
                "id": f"custom_l1_{l1}",
                "name": l1,
                "level": 1,
                "is_leaf": False,
                "marker": "",
                "cell_type_l1": l1,
                "cell_type_l4": None,
                "path": [l1],
            }
        )

    for i, r in table.iterrows():
        l1 = r["cell_type_l1"] if isinstance(r["cell_type_l1"], str) and r["cell_type_l1"] else default_l1
        label = str(r["label"])
        nodes.append(
            {
                "id": f"custom_leaf_{i}_{label}",
                "name": label,
                "level": 4,
                "is_leaf": True,
                "marker": r["marker"],
                "cell_type_l1": l1,
                "cell_type_l2": label,
                "cell_type_l3": label,
                "cell_type_l4": label,
                "path": [l1, label],
            }
        )

    return {
        "source": source_path or "custom_marker_table",
        "source_kind": "custom_marker_table",
        "dataset": "user-provided markers",
        "n_nodes": len(nodes),
        "n_leaves": int(sum(1 for n in nodes if n.get("is_leaf"))),
        "l1_lineages": l1_names,
        "alias_to_canonical": {},
        "edges": [],
        "nodes": nodes,
    }


def merge_ontologies(builtin: dict, custom_table: pd.DataFrame, *, source_path: str | None = None) -> dict:
    """Merge user markers into TrueBlood ontology.

    - Matching leaf *name* → override marker string.
    - New label → add leaf under cell_type_l1 (required).
    """
    import copy

    onto = copy.deepcopy(builtin)
    by_name = {n["name"]: n for n in onto["nodes"]}
    added = 0
    overridden = 0

    for i, r in custom_table.iterrows():
        label = str(r["label"])
        if label in by_name and by_name[label].get("is_leaf"):
            by_name[label]["marker"] = r["marker"]
            overridden += 1
            continue
        l1 = r["cell_type_l1"]
        if not isinstance(l1, str) or not l1:
            raise ValueError(
                f"New custom label '{label}' needs cell_type_l1/l1 for --marker-mode merge "
                f"(or use --marker-mode custom)."
            )
        if l1 not in by_name:
            # allow new L1 bucket
            node_l1 = {
                "id": f"custom_l1_{l1}",
                "name": l1,
                "level": 1,
                "is_leaf": False,
                "marker": "",
                "cell_type_l1": l1,
                "cell_type_l4": None,
                "path": [l1],
            }
            onto["nodes"].append(node_l1)
            by_name[l1] = node_l1
            lineages = list(onto.get("l1_lineages") or [])
            if l1 not in lineages:
                lineages.append(l1)
                onto["l1_lineages"] = lineages

        leaf = {
            "id": f"custom_leaf_{i}_{label}",
            "name": label,
            "level": 4,
            "is_leaf": True,
            "marker": r["marker"],
            "cell_type_l1": l1,
            "cell_type_l2": label,
            "cell_type_l3": label,
            "cell_type_l4": label,
            "path": [l1, label],
        }
        onto["nodes"].append(leaf)
        by_name[label] = leaf
        added += 1

    onto["n_nodes"] = len(onto["nodes"])
    onto["n_leaves"] = int(sum(1 for n in onto["nodes"] if n.get("is_leaf")))
    onto["source_kind"] = "merged_marker_table"
    onto["custom_marker_source"] = source_path
    onto["merge_stats"] = {"overridden": overridden, "added": added}
    return onto


def resolve_ontology(
    *,
    marker_table: str | None,
    marker_mode: str = "builtin",
    ontology_path: str | None = None,
) -> tuple[dict, str | None]:
    """Return (ontology, force_l1).

    force_l1 is \"Custom\" when using a flat custom table with no per-row L1.
    """
    mode = (marker_mode or "builtin").lower()
    if mode not in {"builtin", "custom", "merge"}:
        raise ValueError(f"Unknown marker_mode: {marker_mode!r}")

    builtin = load_ontology(ontology_path)

    if mode == "builtin":
        if marker_table:
            raise ValueError("--marker-table requires --marker-mode custom or merge")
        return builtin, None

    if not marker_table:
        raise ValueError(f"--marker-mode {mode} requires --marker-table")

    table = load_marker_table(marker_table)
    if mode == "custom":
        has_l1 = table["cell_type_l1"].notna().any()
        onto = ontology_from_marker_table(
            table,
            default_l1="Custom",
            source_path=str(marker_table),
        )
        force = None if has_l1 else "Custom"
        return onto, force

    onto = merge_ontologies(builtin, table, source_path=str(marker_table))
    return onto, None


def marker_gene_coverage(adata, onto: dict) -> dict[str, object]:
    """Summarize how many marker genes are present in adata.var_names."""
    var = set(map(str, adata.var_names))
    total_pos = total_neg = hit_pos = hit_neg = 0
    missing: list[str] = []
    for node in onto["nodes"]:
        if not node.get("is_leaf"):
            continue
        pos, neg = parse_marker_string(node.get("marker") or "")
        total_pos += len(pos)
        total_neg += len(neg)
        for g in pos:
            if g in var:
                hit_pos += 1
            else:
                missing.append(g)
        for g in neg:
            if g in var:
                hit_neg += 1
            else:
                missing.append(g)
    # unique missing, preserve order
    seen = set()
    missing_u = []
    for g in missing:
        if g not in seen:
            seen.add(g)
            missing_u.append(g)
    return {
        "leaf_markers_pos": total_pos,
        "leaf_markers_neg": total_neg,
        "present_pos": hit_pos,
        "present_neg": hit_neg,
        "missing_genes": missing_u[:40],
        "n_missing": len(missing_u),
    }
