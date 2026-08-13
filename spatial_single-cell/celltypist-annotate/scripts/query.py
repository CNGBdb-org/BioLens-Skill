#!/usr/bin/env python3
"""CellTypist annotation CLI for BioLens spatial_single-cell skill."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _boot() -> None:
    here = Path(__file__).resolve().parent
    for p in here.parents:
        if (p / "scverse_common").is_dir():
            sys.path.insert(0, str(p))
            return


_boot()

from scverse_common.io import load_adata, save_adata  # noqa: E402
from scverse_common.report import ensure_outdir, print_header, write_report  # noqa: E402


def _require_celltypist():
    try:
        import celltypist
        from celltypist import models
    except ImportError as exc:  # noqa: BLE001
        raise SystemExit(
            "缺少 celltypist。请安装：pip install celltypist\n"
            "或：pip install -r ../../requirements.txt"
        ) from exc
    return celltypist, models


def _looks_like_counts(adata) -> bool:
    """Heuristic: max value >> log1p scale suggests raw / unnormalized counts."""
    import numpy as np
    from scipy import sparse

    X = adata.X
    if sparse.issparse(X):
        if X.nnz == 0:
            return False
        # sample up to 100k nonzeros
        data = X.data
        if data.size > 100_000:
            data = data[:100_000]
        mx = float(np.max(data))
    else:
        mx = float(np.max(X)) if X.size else 0.0
    return mx > 20.0


def _auto_normalize(adata):
    import scanpy as sc

    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    return adata


def cmd_models(args: argparse.Namespace) -> None:
    celltypist, models = _require_celltypist()
    print_header("celltypist-annotate", "list models")
    try:
        desc = models.models_description(on_the_fly=not args.local)
    except Exception:  # noqa: BLE001
        desc = models.models_description()
    print(desc.to_string(index=False) if hasattr(desc, "to_string") else desc)
    print(f"\nlocal models path: {models.models_path}")
    print(f"celltypist version: {celltypist.__version__}")


def cmd_download(args: argparse.Namespace) -> None:
    _, models = _require_celltypist()
    print_header("celltypist-annotate", "download models")
    if args.all:
        models.download_models(force_update=args.force)
        print("downloaded: all models")
    else:
        model = args.model or "Immune_All_Low.pkl"
        models.download_models(model=model, force_update=args.force)
        print(f"downloaded: {model}")
    print(f"local models path: {models.models_path}")


def _ensure_model(models, model: str) -> None:
    try:
        models.Model.load(model=model)
    except Exception:  # noqa: BLE001
        print(f"model not found locally; downloading {model} …")
        models.download_models(model=model)


def _annotate_input(
    indata,
    *,
    model: str,
    majority_voting: bool,
    over_clustering: str | None,
    mode: str,
    auto_normalize: bool,
    p_thres: float,
    skip_count_check: bool = False,
):
    """indata: AnnData or path accepted by celltypist.annotate (h5ad/csv)."""
    celltypist, models = _require_celltypist()
    _ensure_model(models, model)

    note = None
    # AnnData path: optional count check / normalize
    is_adata = hasattr(indata, "obs") and hasattr(indata, "X")
    if is_adata and not skip_count_check and _looks_like_counts(indata):
        if auto_normalize:
            indata = indata.copy()
            _auto_normalize(indata)
            note = "auto-normalized: normalize_total(1e4) + log1p"
        else:
            raise SystemExit(
                "输入看起来像未 normalize 的 counts（max>20）。\n"
                "请先跑 scanpy-preprocess，或加 --auto-normalize。"
            )

    kwargs = {
        "model": model,
        "majority_voting": majority_voting,
        "mode": mode,
        "p_thres": p_thres,
    }
    if majority_voting and over_clustering:
        if not is_adata:
            raise SystemExit("--over-clustering 仅支持 AnnData / h5ad 输入")
        if over_clustering not in indata.obs.columns:
            raise SystemExit(
                f"--over-clustering '{over_clustering}' 不在 adata.obs 中。"
                f"可用列：{list(indata.obs.columns)}"
            )
        kwargs["over_clustering"] = over_clustering

    predictions = celltypist.annotate(indata, **kwargs)
    return predictions, note, celltypist


def cmd_annotate(args: argparse.Namespace) -> None:
    out = ensure_outdir(args.outdir, "celltypist_annotate")
    print_header("celltypist-annotate", args.input)
    path = Path(args.input)
    if path.suffix.lower() == ".csv":
        indata = str(path)
    else:
        indata = load_adata(args.input)

    predictions, note, celltypist = _annotate_input(
        indata,
        model=args.model,
        majority_voting=args.majority_voting,
        over_clustering=args.over_clustering,
        mode=args.mode,
        auto_normalize=args.auto_normalize,
        p_thres=args.p_thres,
    )

    # tables
    predictions.to_table(folder=str(out / "tables"), prefix="")
    # annotated adata
    insert_conf_by = "majority_voting" if args.majority_voting else "predicted_labels"
    adata_out = predictions.to_adata(
        insert_labels=True,
        insert_conf=True,
        insert_conf_by=insert_conf_by,
    )
    h5ad_path = save_adata(adata_out, out / "celltypist_annotated.h5ad")

    # plots (best-effort; needs embedding sometimes)
    plot_ok = False
    try:
        predictions.to_plots(folder=str(out / "figures"), plot_probability_to_majority_voting=True)
        plot_ok = True
    except Exception as exc:  # noqa: BLE001
        print(f"  plots skipped: {exc}")

    labels = predictions.predicted_labels
    label_col = "majority_voting" if (args.majority_voting and "majority_voting" in labels.columns) else "predicted_labels"
    vc = labels[label_col].value_counts()
    summary_csv = out / "tables" / "label_counts.csv"
    vc.rename("n_cells").to_csv(summary_csv, header=True)

    lines = [
        f"- input: `{args.input}`",
        f"- model: `{args.model}`",
        f"- majority_voting: {args.majority_voting}",
        f"- over_clustering: `{args.over_clustering or 'auto/none'}`",
        f"- mode: `{args.mode}`",
        f"- celltypist: {celltypist.__version__}",
        f"- n_obs: {adata_out.n_obs}",
        f"- label column: `{label_col}`",
        f"- output h5ad: `{h5ad_path.name}`",
        f"- tables: `tables/`",
        f"- label counts: `tables/label_counts.csv`",
        f"- plots: `{'figures/' if plot_ok else 'skipped'}`",
        "- top labels:",
    ]
    if note:
        lines.insert(5, f"- note: {note}")
    for name, n in vc.head(15).items():
        lines.append(f"  - {name}: {int(n)}")

    write_report(out, "celltypist-annotate", lines)
    print(vc.head(12).to_string())
    print(f"  h5ad: {h5ad_path}")
    print(f"  report: {out / 'report.md'}")


def cmd_demo(args: argparse.Namespace) -> None:
    celltypist, _ = _require_celltypist()
    sample = celltypist.samples.get_sample_csv()
    class _A:
        input = sample
        outdir = args.outdir
        model = args.model
        majority_voting = args.majority_voting
        over_clustering = None
        mode = "best match"
        auto_normalize = False
        p_thres = 0.5

    print_header("celltypist-annotate", f"demo → {sample}")
    cmd_annotate(_A())


def main() -> None:
    ap = argparse.ArgumentParser(
        description="CellTypist cell type annotation (list / download / annotate)"
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_models = sub.add_parser("models", help="List available CellTypist models")
    p_models.add_argument(
        "--local",
        action="store_true",
        help="Only show locally cached model metadata",
    )
    p_models.set_defaults(func=cmd_models)

    p_dl = sub.add_parser("download", help="Download model(s) to local cache")
    p_dl.add_argument("--model", default=None, help="Model filename (default Immune_All_Low.pkl)")
    p_dl.add_argument("--all", action="store_true", help="Download all models")
    p_dl.add_argument("--force", action="store_true", help="Force re-download")
    p_dl.set_defaults(func=cmd_download)

    p_ann = sub.add_parser("annotate", help="Annotate an h5ad / matrix with CellTypist")
    p_ann.add_argument("input", help="Input h5ad / 10x h5 / 10x mtx dir")
    p_ann.add_argument("-o", "--outdir", default=None)
    p_ann.add_argument("--model", default="Immune_All_Low.pkl")
    p_ann.add_argument(
        "--majority-voting",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Refine labels by over-clustering majority vote (default: on)",
    )
    p_ann.add_argument(
        "--over-clustering",
        default=None,
        help="obs column for majority voting (e.g. leiden); default=CellTypist heuristic",
    )
    p_ann.add_argument("--mode", default="best match", choices=["best match", "prob match"])
    p_ann.add_argument("--p-thres", type=float, default=0.5, help="For mode=prob match")
    p_ann.add_argument(
        "--auto-normalize",
        action="store_true",
        help="If input looks like counts, run normalize_total(1e4)+log1p",
    )
    p_ann.set_defaults(func=cmd_annotate)

    p_demo = sub.add_parser("demo", help="Run annotation on CellTypist built-in sample CSV")
    p_demo.add_argument("-o", "--outdir", default=None)
    p_demo.add_argument("--model", default="Immune_All_Low.pkl")
    p_demo.add_argument(
        "--majority-voting",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    p_demo.set_defaults(func=cmd_demo)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
