#!/usr/bin/env python3
"""Obs-group spot landscape across developmental stages."""

import argparse
import collections
import json
import os
import sys

import numpy as np

from bootstrap import prepare_atlas_paths
from atlas_registry import DEFAULT_OBS_LABEL, get_atlas
import catalog_bridge as cat
from io_core import load_obs_column, setup_matplotlib, validate_dataset_dir

prepare_atlas_paths()


def aggregate_landscape(*, max_per_stage=3, organ_focus=None):
    spec = get_atlas()
    catalog = cat.load_catalog()
    if spec.name == "hesta":
        if hasattr(cat, "is_sagittal_section"):
            catalog = [e for e in catalog if cat.is_sagittal_section(e)]
        else:
            catalog = [e for e in catalog if cat.is_primary_section(e)]
    else:
        catalog = [e for e in catalog if cat.is_sagittal_section(e)]

    by_stage = collections.defaultdict(list)
    for e in catalog:
        by_stage[e.stage].append(e)
    for st in by_stage:
        by_stage[st].sort(key=lambda e: (-len(e.tissues), e.section))

    stage_organ = collections.defaultdict(lambda: collections.Counter())
    stage_totals = collections.Counter()
    samples_used = []

    stage_order = cat.STAGE_ORDER if hasattr(cat, "STAGE_ORDER") else sorted(by_stage.keys(), key=str)
    for stage in stage_order:
        entries = by_stage.get(stage, [])[:max_per_stage]
        for e in entries:
            try:
                ds = validate_dataset_dir(e.dataset_id)
                labels = load_obs_column(ds, DEFAULT_OBS_LABEL)
            except FileNotFoundError:
                continue
            samples_used.append({"stage": stage, "dataset_id": e.dataset_id, "section": e.section})
            c = collections.Counter(labels)
            stage_totals[stage] += sum(c.values())
            for organ, n in c.items():
                if organ_focus and organ_focus.lower() not in str(organ).lower():
                    continue
                stage_organ[stage][organ] += n

    if not samples_used and by_stage:
        for stage in sorted(by_stage.keys(), key=cat.stage_sort_key if hasattr(cat, "stage_sort_key") else str):
            for e in by_stage[stage][:max_per_stage]:
                try:
                    ds = validate_dataset_dir(e.dataset_id)
                    labels = load_obs_column(ds, DEFAULT_OBS_LABEL)
                except FileNotFoundError:
                    continue
                samples_used.append({"stage": stage, "dataset_id": e.dataset_id, "section": e.section})
                c = collections.Counter(labels)
                stage_totals[stage] += sum(c.values())
                for organ, n in c.items():
                    if organ_focus and organ_focus.lower() not in str(organ).lower():
                        continue
                    stage_organ[stage][organ] += n

    return stage_organ, stage_totals, samples_used


def _write_plot(stage_organ, stage_totals, *, organ_focus, output_path, dpi=100):
    spec = get_atlas()
    stages = sorted(stage_organ.keys(), key=str)
    plt = setup_matplotlib()
    scale = max(1.0, dpi / 100.0)
    if organ_focus:
        ys = []
        for st in stages:
            ctr = stage_organ[st]
            total = stage_totals[st] or 1
            n = sum(v for o, v in ctr.items() if organ_focus.lower() in str(o).lower())
            ys.append(100 * n / total)
        fig, ax = plt.subplots(figsize=(8 * scale, 4 * scale))
        ax.plot(stages, ys, marker="o", color="#E64B35")
        ax.set_ylabel(f"{organ_focus} spot %", fontsize=10 * scale)
        ax.set_title(f"{organ_focus} across {spec.display_name} stages", fontsize=12 * scale)
    else:
        organs = sorted(
            {o for ctr in stage_organ.values() for o in ctr},
            key=lambda o: -sum(stage_organ[st].get(o, 0) for st in stages),
        )[:10]
        mat = np.zeros((len(organs), len(stages)))
        for j, st in enumerate(stages):
            total = stage_totals[st] or 1
            for i, o in enumerate(organs):
                mat[i, j] = 100 * stage_organ[st].get(o, 0) / total
        fig, ax = plt.subplots(figsize=(10 * scale, 6 * scale))
        im = ax.imshow(mat, aspect="auto", cmap="Blues")
        ax.set_xticks(range(len(stages)))
        ax.set_xticklabels(stages, rotation=45, ha="right", fontsize=8 * scale)
        ax.set_yticks(range(len(organs)))
        ax.set_yticklabels(organs, fontsize=max(8, int(8 * scale)))
        ax.set_title(f"Top {DEFAULT_OBS_LABEL} spot % by stage", fontsize=12 * scale)
        fig.colorbar(im, ax=ax, shrink=0.7)
    import matplotlib.pyplot as plt_module
    plt_module.tight_layout()
    fig.savefig(output_path, bbox_inches="tight", facecolor="white", dpi=dpi)
    plt.close(fig)
    print(f"Saved: {output_path}")


def main():
    spec = get_atlas()
    p = argparse.ArgumentParser(description=f"{DEFAULT_OBS_LABEL} abundance across stages.")
    p.add_argument("--organ", "-O")
    p.add_argument("--max-per-stage", type=int, default=3 if spec.name == "hesta" else 2)
    p.add_argument("-o", "--output", default=None)
    p.add_argument("--format", choices=["text", "json"], default="text")
    p.add_argument("--plot", action="store_true")
    p.add_argument("--dpi", type=int, default=100)
    args = p.parse_args()

    stage_organ, stage_totals, samples = aggregate_landscape(
        max_per_stage=args.max_per_stage,
        organ_focus=args.organ,
    )

    if args.format == "json":
        print(json.dumps({
            "samples": samples,
            "by_stage": {
                st: {o: {"spots": n, "pct": round(100 * n / stage_totals[st], 2)} for o, n in ctr.most_common()}
                for st, ctr in stage_organ.items()
            },
        }, indent=2, ensure_ascii=False))
    else:
        print(f"Landscape ({len(samples)} samples, max {args.max_per_stage}/stage)\n")
        if args.organ:
            print(f"{'stage':<12} {'pct%':>8}  {'spots':>10}")
            for st in sorted(stage_organ.keys(), key=str):
                ctr = stage_organ[st]
                total = stage_totals[st] or 1
                n = sum(v for o, v in ctr.items() if args.organ.lower() in str(o).lower())
                print(f"{st:<12} {100 * n / total:>8.1f}  {n:>10,}")
        else:
            all_organs = sorted({o for ctr in stage_organ.values() for o in ctr})
            top_organs = all_organs[:15]
            print(f"{'stage':<12}" + "".join(f"{o[:10]:>12}" for o in top_organs))
            for st in sorted(stage_organ.keys(), key=str):
                ctr = stage_organ[st]
                total = stage_totals[st] or 1
                vals = [100 * ctr.get(o, 0) / total for o in top_organs]
                print(f"{st:<12}" + "".join(f"{v:>12.1f}" for v in vals))

    if args.plot:
        out = args.output or os.path.join(os.getcwd(), "organ_stage_landscape.png")
        _write_plot(
            stage_organ, stage_totals,
            organ_focus=args.organ, output_path=out, dpi=args.dpi,
        )


if __name__ == "__main__":
    main()
