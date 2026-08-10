#!/usr/bin/env python3
"""CIMA-CLM Demo: in silico mutagenesis variant effect prediction (standalone script).

Uses pre-computed Enformer predictions — no GPU or model weights required.
Generates: variant CSV (+3 alt alleles per position), heatmap, line chart, sequence logo.

Usage:
    python ./scripts/run_demo.py /path/to/CIMA-CLM_Demo
    CIMA_CLM_DEMO=/path/to/CIMA-CLM_Demo python ./scripts/run_demo.py --out ./my_output
"""

import argparse, os, sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import seaborn as sns

# ── defaults ──────────────────────────────────────────────────────────
# Demo data is NOT shipped; pass path or set CIMA_CLM_DEMO
_DEFAULT_DEMO = os.environ.get("CIMA_CLM_DEMO", "")


def parse_args():
    p = argparse.ArgumentParser(description="CIMA-CLM in silico mutagenesis demo")
    p.add_argument("data_dir", nargs="?", default=_DEFAULT_DEMO or None,
                   help="Path to CIMA-CLM_Demo directory (or set env CIMA_CLM_DEMO)")
    p.add_argument("--out", default=None, help="Output directory (default: <data_dir>/output)")
    return p.parse_args()


def ensure_data(data_dir):
    """Verify required input files exist."""
    required = [
        "Switched_Bm_IGHDnegchr22_39351775_150bp.csv",
        "Switched_Bm_IGHDneg_silicon_results.csv",
    ]
    missing = [f for f in required if not os.path.isfile(os.path.join(data_dir, f))]
    if missing:
        sys.exit(f"Missing input files in {data_dir}: {missing}")
    optional = "variant_Switched_Bm_IGHDnegx_mean.csv"
    if os.path.isfile(os.path.join(data_dir, optional)):
        print(f"  [skip] pre-computed mean file found: {optional}")
    print(f"  Data dir: {data_dir}")


# ── Cell 1: In silico mutagenesis — generate all alt alleles ──────────
def generate_variants(data_dir, out_dir):
    print("\n[1/4] Generating variant sequences (in silico mutagenesis) ...")
    df = pd.read_csv(os.path.join(data_dir, "Switched_Bm_IGHDnegchr22_39351775_150bp.csv"))
    df = df.reset_index().rename(columns={"index": "index"})
    nucleotides = ["A", "C", "G", "T"]

    new_rows = []
    for idx, row in df.iterrows():
        seq = row["sequence"]
        pos = row["snp_relative_pos"]
        ref_nuc = seq[pos]
        # 3 alt alleles
        for nuc in nucleotides:
            if nuc != ref_nuc:
                nr = row.copy()
                nr["sequence"] = seq[:pos] + nuc + seq[pos + 1:]
                nr["group"] = "alt"
                nr["nuc"] = nuc
                new_rows.append(nr)
        # ref allele
        orig = row.copy()
        orig["group"] = "ref"
        orig["nuc"] = ref_nuc
        new_rows.append(orig)

    new_df = pd.DataFrame(new_rows)
    new_df["pos"] = new_df.apply(
        lambda r: f"{r['variant_id']}_{r['nuc']}_{r['group']}", axis=1
    )
    new_df = new_df.sort_values(by=["index", "group"], ascending=[True, False]).reset_index(drop=True)

    variant_seq_df = pd.DataFrame({
        "index": new_df["index"],
        "nuc": new_df["nuc"],
        "group": new_df["group"],
        "seq": new_df["sequence"],
        "pos": new_df["pos"],
        "sample": new_df["sample_id"],
        "variant_id": new_df["variant_id"],
    })
    out_path = os.path.join(out_dir, "Switched_Bm_IGHDneg.csv")
    variant_seq_df.to_csv(out_path, index=False)
    print(f"  {len(variant_seq_df)} variant rows → {out_path}")


# ── Cell 3+5: Merge predictions, compute alt-ref diff, mean across individuals ─
def postprocess_predictions(data_dir, out_dir):
    print("\n[2/4] Merging pre-computed predictions, computing alt-ref differences ...")

    # Check if pre-computed mean already exists
    pre_mean = os.path.join(data_dir, "variant_Switched_Bm_IGHDnegx_mean.csv")
    if os.path.isfile(pre_mean):
        import shutil
        shutil.copy2(pre_mean, os.path.join(out_dir, "variant_Switched_Bm_IGHDnegx_mean.csv"))
        print(f"  Using pre-computed mean from {pre_mean}")
        return

    # Otherwise compute from silicon results
    variant_df = pd.read_csv(os.path.join(out_dir, "Switched_Bm_IGHDneg.csv"))
    silicon_df = pd.read_csv(os.path.join(data_dir, "Switched_Bm_IGHDneg_silicon_results.csv"))

    # Merge: variant metadata (pos, nuc, group) with prediction
    merged = variant_df.merge(silicon_df[["index", "pred_peak_value"]], on="index", how="inner")

    # Pivot: rows=position×sample×variant_id, cols=group (ref/alt)
    pivot = merged.pivot_table(
        index=["sample", "variant_id", "snp_relative_pos", "nuc"],
        columns="group",
        values="pred_peak_value",
    ).reset_index()
    pivot.columns.name = None

    # alt - ref difference
    pivot["diff"] = pivot["alt"] - pivot["ref"]

    # Mean across individuals per position × nucleotide
    mean_df = pivot.pivot_table(
        index=["variant_id", "snp_relative_pos"],
        columns="nuc",
        values="diff",
    ).reset_index()
    mean_df.columns = [
        "variant_id", "snp_relative_pos",
        "mean_base_A_pred_peak", "mean_base_C_pred_peak",
        "mean_base_G_pred_peak", "mean_base_T_pred_peak",
    ]

    out_path = os.path.join(out_dir, "variant_Switched_Bm_IGHDnegx_mean.csv")
    mean_df.to_csv(out_path, index=False)
    print(f"  {len(mean_df)} positions → {out_path}")


# ── Cell 7: Heatmap ───────────────────────────────────────────────────
def plot_heatmap(out_dir):
    print("\n[3/4] Plotting heatmap ...")
    df_mean = pd.read_csv(os.path.join(out_dir, "variant_Switched_Bm_IGHDnegx_mean.csv"))

    records = []
    for _, row in df_mean.iterrows():
        pos = row["snp_relative_pos"]
        records.append([pos, "A", row["mean_base_A_pred_peak"]])
        records.append([pos, "T", row["mean_base_T_pred_peak"]])
        records.append([pos, "C", row["mean_base_C_pred_peak"]])
        records.append([pos, "G", row["mean_base_G_pred_peak"]])
    ndf = pd.DataFrame(records, columns=["index", "nuc", "pred_peak_value"])

    data = ndf[(ndf["index"] >= 200) & (ndf["index"] <= 300)]
    hm = data.pivot(index="nuc", columns="index", values="pred_peak_value")

    plt.figure(figsize=(20, 3))
    cmap = LinearSegmentedColormap.from_list("custom_cmap", ["blue", "white", "red"])
    sns.heatmap(hm, cmap=cmap, center=0, vmin=-3, vmax=3)
    path = os.path.join(out_dir, "heatmap.pdf")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  → {path}")


# ── Cell 9: Line chart ────────────────────────────────────────────────
def plot_line_chart(out_dir):
    print("[4/4] Plotting line chart ...")
    df_mean = pd.read_csv(os.path.join(out_dir, "variant_Switched_Bm_IGHDnegx_mean.csv"))
    df_sub = df_mean[(df_mean["snp_relative_pos"] >= 200) & (df_mean["snp_relative_pos"] <= 300)]

    plt.figure(figsize=(12, 6))
    for base, color in [("A", "green"), ("T", "red"), ("G", "yellow"), ("C", "blue")]:
        col = f"mean_base_{base}_pred_peak"
        if col in df_sub.columns:
            plt.plot(df_sub["snp_relative_pos"], df_sub[col], color=color, label=base)

    plt.ylim(-3, 3)
    plt.xlabel("Position")
    plt.ylabel("Alt − Ref (predicted expression change)")
    plt.legend()
    plt.axvline(x=250, color="gray", linestyle="--")
    ax = plt.gca()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    path = os.path.join(out_dir, "linechart.pdf")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  → {path}")

    # Sequence logo (optional, requires logomaker)
    try:
        import logomaker as lm

        def keep_max_abs(row):
            abs_vals = row[1:].abs()
            max_idx = abs_vals.idxmax()
            nr = row.copy()
            nr.loc[nr.index != max_idx] = 0
            return nr

        df_lm = df_mean.apply(keep_max_abs, axis=1)
        df_lm["position"] = df_mean["snp_relative_pos"]
        df_sub2 = df_lm[(df_lm["position"] >= 200) & (df_lm["position"] <= 300)]
        df_sub2 = df_sub2.set_index("position").rename(columns={
            "mean_base_A_pred_peak": "A", "mean_base_T_pred_peak": "T",
            "mean_base_C_pred_peak": "C", "mean_base_G_pred_peak": "G",
        })[["A", "C", "G", "T"]]

        plt.figure(figsize=(10, 3))
        lm.Logo(df_sub2, color_scheme="classic")
        plt.axvline(x=250, color="gray", linestyle="--", linewidth=1)
        plt.xlim(200, 300)
        plt.ylim(-3, 3)
        path2 = os.path.join(out_dir, "seq_logo.pdf")
        plt.savefig(path2, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  → {path2}")
    except ImportError:
        print("  [skip] Sequence logo skipped (logomaker not installed)")


# ── main ──────────────────────────────────────────────────────────────
def main():
    args = parse_args()
    if not args.data_dir:
        sys.exit("ERROR: provide CIMA-CLM_Demo path as argument or set CIMA_CLM_DEMO")
    data_dir = os.path.abspath(args.data_dir)
    out_dir = args.out or os.path.join(data_dir, "output")
    os.makedirs(out_dir, exist_ok=True)

    ensure_data(data_dir)

    generate_variants(data_dir, out_dir)
    postprocess_predictions(data_dir, out_dir)
    plot_heatmap(out_dir)
    plot_line_chart(out_dir)

    print(f"\nDone. Outputs in: {out_dir}")
    for f in sorted(os.listdir(out_dir)):
        size = os.path.getsize(os.path.join(out_dir, f))
        print(f"  {f:50s} {size:>10,} bytes")


if __name__ == "__main__":
    main()
