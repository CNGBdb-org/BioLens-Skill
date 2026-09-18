#!/usr/bin/env python3
"""Virus receptor expression across atlas samples."""

import argparse
import json
import os
import sys

import numpy as np

from bootstrap import prepare_atlas_paths
from atlas_registry import DEFAULT_OBS_LABEL, get_atlas
from gene_map_core import gene_group_matrix, pick_atlas_samples, top_hits
from gene_stats_core import summarize_gene
from gene_tables_bridge import virus_receptors
from io_core import setup_matplotlib, validate_dataset_dir

prepare_atlas_paths()

DEFAULT_STAGES = {
    "hesta": "CS12-13,CS14-15,CS17,CS18,CS19,CS20,CS23",
    "mosta": "E9.5,E12.5,E16.5",
    "mccsta": "T402,T530,T550",
}


def main():
    spec = get_atlas()
    VIRUS_RECEPTORS = virus_receptors()
    p = argparse.ArgumentParser(description=f"Virus receptor map ({spec.display_name}).")
    p.add_argument("--pathogen", "-p", default="all")
    p.add_argument("data_dir", nargs="?", help="Single sample (optional)")
    p.add_argument("--stages", default=DEFAULT_STAGES[spec.name])
    p.add_argument("--max-per-stage", type=int, default=1)
    p.add_argument("--top", type=int, default=5)
    p.add_argument("-o", "--output", default=None)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--plot", action="store_true")
    args = p.parse_args()

    if args.pathogen.lower() == "all":
        pathogens = list(VIRUS_RECEPTORS.keys())
    else:
        key = next((k for k in VIRUS_RECEPTORS if k.lower() == args.pathogen.lower()), None)
        if not key:
            print(f"Unknown pathogen. Choose: {', '.join(VIRUS_RECEPTORS)}", file=sys.stderr)
            sys.exit(1)
        pathogens = [key]

    rows = []
    focus_key = "organs_focus" if spec.name == "hesta" else "annotations_focus"
    if spec.name == "mccsta":
        focus_key = "annotations_focus"

    if args.data_dir:
        ds = validate_dataset_dir(args.data_dir)
        for pathogen in pathogens:
            info = VIRUS_RECEPTORS[pathogen]
            for gene in info["genes"]:
                try:
                    data = summarize_gene(ds.dataset_id, gene, group_by=DEFAULT_OBS_LABEL)
                except FileNotFoundError:
                    continue
                for item in data.get("by_" + DEFAULT_OBS_LABEL, []):
                    rows.append({
                        "pathogen": pathogen,
                        "gene": data["gene"],
                        "dataset_id": ds.dataset_id,
                        "stage": ds.meta.stage if ds.meta else "?",
                        "organ": item[DEFAULT_OBS_LABEL],
                        "mean_expression": item["mean_expression"],
                        "pct_expressing": item["pct_expressing"],
                    })
    else:
        entries = pick_atlas_samples(stages=args.stages, max_per_stage=args.max_per_stage)
        for pathogen in pathogens:
            info = VIRUS_RECEPTORS[pathogen]
            sub = gene_group_matrix(entries, info["genes"], groups_focus=info.get(focus_key))
            for r in sub:
                r["pathogen"] = pathogen
                rows.append(r)

    if args.format == "json":
        print(json.dumps({"rows": rows, "top": top_hits(rows, top=args.top)}, indent=2, ensure_ascii=False))
        return

    print(f"Virus receptor expression ({spec.display_name})\n")
    for pathogen in pathogens:
        info = VIRUS_RECEPTORS[pathogen]
        print(f"## {pathogen} — {', '.join(info['genes'])}")
        pr = [r for r in rows if r.get("pathogen") == pathogen]
        for gene, hits in top_hits(pr, top=args.top).items():
            print(f"\n  {gene}:")
            for h in hits:
                print(
                    f"    {h.get('stage', '?'):<10} {h['organ']:<22} "
                    f"mean={h['mean_expression']:.4f}  pct={h['pct_expressing']:.1f}%  ({h.get('dataset_id', '')})"
                )
        print()

    if args.plot and rows:
        out = args.output or os.path.join(os.getcwd(), "virus_receptor_heatmap.png")
        genes = sorted({r["gene"] for r in rows})
        stages = sorted({r.get("stage", "?") for r in rows}, key=str)
        mat = np.zeros((len(genes), len(stages)))
        for i, g in enumerate(genes):
            for j, st in enumerate(stages):
                vals = [r["mean_expression"] for r in rows if r["gene"] == g and r.get("stage") == st]
                mat[i, j] = max(vals) if vals else 0
        plt = setup_matplotlib()
        fig, ax = plt.subplots(figsize=(max(6, len(stages) * 1.2), max(4, len(genes) * 0.5)))
        im = ax.imshow(mat, aspect="auto", cmap="YlOrRd")
        ax.set_xticks(range(len(stages)))
        ax.set_xticklabels(stages, rotation=45, ha="right")
        ax.set_yticks(range(len(genes)))
        ax.set_yticklabels(genes)
        ax.set_title("Virus receptor max mean expression by stage")
        fig.colorbar(im, ax=ax, shrink=0.8)
        import matplotlib.pyplot as plt_module
        plt_module.tight_layout()
        fig.savefig(out, bbox_inches="tight", facecolor="white")
        plt.close(fig)
        print(f"Saved: {out}")


if __name__ == "__main__":
    main()
