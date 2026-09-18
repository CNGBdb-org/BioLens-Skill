#!/usr/bin/env python3
"""Track one gene across catalog samples / stages."""

import argparse
import json
import os
import sys

from bootstrap import prepare_atlas_paths
from atlas_registry import DEFAULT_OBS_LABEL, get_atlas
import catalog_bridge as cat
from gene_map_core import pick_atlas_samples
from gene_stats_core import summarize_gene
from io_core import setup_matplotlib

prepare_atlas_paths()


def pick_samples(*, stages=None, max_per_stage=2, tissue=None):
    if get_atlas().name == "hesta":
        return pick_atlas_samples(stages=stages, max_per_stage=max_per_stage, tissue=tissue)
    return pick_atlas_samples(stages=stages, max_per_stage=max_per_stage)


def main():
    spec = get_atlas()
    p = argparse.ArgumentParser(description=f"Gene expression across {spec.display_name} samples.")
    p.add_argument("-g", "--gene", required=True)
    p.add_argument("--stages", help="Comma-separated stages")
    p.add_argument("--tissue", help="Catalog tissue filter (HESTA)")
    p.add_argument("--samples", help="Comma-separated dataset ids")
    p.add_argument("--max-per-stage", type=int, default=2)
    p.add_argument("--by", default=DEFAULT_OBS_LABEL)
    p.add_argument("--region", help="Mean within this obs group only")
    p.add_argument("--organ", help="Alias for --region")
    p.add_argument("-o", "--output", default=None)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--plot", action="store_true")
    p.add_argument("--dpi", type=int, default=100)
    args = p.parse_args()

    region = args.region or args.organ

    if args.samples:
        entries = []
        for q in args.samples.split(","):
            q = q.strip()
            if not q:
                continue
            did, meta = cat.resolve_dataset_ref(q)
            entries.append(meta or type("E", (), {"dataset_id": did, "section": q, "stage": "?"})())
    else:
        entries = pick_samples(stages=args.stages, max_per_stage=args.max_per_stage, tissue=args.tissue)

    rows = []
    prefix = spec.api_prefix
    for e in entries:
        did = e.dataset_id
        try:
            if region:
                data = summarize_gene(did, args.gene, group_by=args.by, filter_groups=[region])
                groups = data.get("by_" + args.by, [])
                if groups:
                    mean = groups[0]["mean_expression"]
                    pct = groups[0]["pct_expressing"]
                else:
                    mean, pct = 0, 0
            else:
                data = summarize_gene(did, args.gene, group_by=None)
                mean = data["mean_all_spots"]
                pct = data["pct_expressing"]
            rows.append({
                "dataset_id": did,
                "section": getattr(e, "section", did),
                "stage": getattr(e, "stage", "?"),
                "mean_expression": mean,
                "pct_expressing": pct,
                "n_spots": data["n_spots"],
                "gene": data["gene"],
            })
        except FileNotFoundError as ex:
            rows.append({"dataset_id": did, "section": getattr(e, "section", did), "error": str(ex)})

    gene = rows[0].get("gene", args.gene) if rows and "gene" in rows[0] else args.gene
    if args.format == "json":
        print(json.dumps({"gene": gene, "results": rows}, indent=2, ensure_ascii=False))
    else:
        print(f"Gene: {gene}  |  samples: {len(rows)}\n")
        sw = 10 if spec.name == "hesta" else 8
        print(f"{'stage':<{sw}} {'mean':>10} {'pct%':>8}  dataset")
        for r in rows:
            if "error" in r:
                print(f"{r.get('stage','?'):<{sw}} {'—':>10} {'—':>8}  {r['dataset_id']}  [skip]")
            else:
                print(f"{r['stage']:<{sw}} {r['mean_expression']:>10.4f} {r['pct_expressing']:>8.1f}  {r['dataset_id']}")

    if args.plot and rows:
        valid = [r for r in rows if "error" not in r]
        if not valid:
            return
        out = args.output or os.path.join(os.getcwd(), f"gene_across_{gene}.png")
        means = [r["mean_expression"] for r in valid]
        plt = setup_matplotlib()
        scale = max(1.0, args.dpi / 100.0)
        fig, ax = plt.subplots(figsize=(max(8, len(valid) * 0.5) * scale, 5 * scale))
        color = "#3C5488" if spec.name == "hesta" else "#4DBBD5"
        ax.bar(range(len(valid)), means, color=color)
        ax.set_xticks(range(len(valid)))
        ax.set_xticklabels(
            [f"{r['stage']}\n{r['dataset_id'].replace(prefix, '')}" for r in valid],
            fontsize=max(6, int(6 * scale)), rotation=45, ha="right",
        )
        ylab = "mean expression" + (f" in {region}" if region else "")
        ax.set_ylabel(ylab, fontsize=10 * scale)
        ax.set_title(f"{gene} across {spec.display_name} samples", fontsize=12 * scale)
        import matplotlib.pyplot as plt_module
        plt_module.tight_layout()
        fig.savefig(out, bbox_inches="tight", facecolor="white", dpi=args.dpi)
        plt.close(fig)
        print(f"Saved: {out}")


if __name__ == "__main__":
    main()
