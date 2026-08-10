#!/usr/bin/env python3
"""Print dataset schema summary."""

import argparse
import json
import sys

from bootstrap import prepare_atlas_paths

prepare_atlas_paths()

from io_core import load_schema, sample_name, validate_dataset_dir


def main():
    p = argparse.ArgumentParser(description="Summarize parquet dataset metadata.")
    p.add_argument("data_dir")
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    ds = validate_dataset_dir(args.data_dir)
    s = load_schema(ds)
    meta = ds.meta
    info = {
        "sample": sample_name(ds),
        "dataset_id": ds.dataset_id,
        "shape": s.get("shape"),
        "n_genes": len(s.get("var", [])),
        "obs_numeric": s.get("obs", []),
        "obs_categorical": s.get("obsCat", []),
        "embeddings": [e.get("name") for e in s.get("embeddings", [])],
        "marker_groups": sorted({str(m.get("name")) for m in s.get("markers", [])}),
        "color_fields": list(s.get("colors", {}).keys()),
    }
    if meta:
        info["catalog"] = {
            "section": meta.section,
            "stage": meta.stage,
            "tissues": meta.tissues,
            "sex": meta.sex,
            "technology": meta.technology,
        }

    if args.format == "json":
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return

    n_obs, n_var = info["shape"]
    print(f"Sample: {info['sample']}")
    if meta:
        print(f"Stage:  {meta.stage}  |  Sex: {meta.sex}  |  Tech: {meta.technology}")
        print(f"Section: {meta.section}")
        if meta.tissues:
            print(f"Tissues ({len(meta.tissues)}): {', '.join(meta.tissues[:12])}" + (" ..." if len(meta.tissues) > 12 else ""))
    print(f"Shape:  {n_obs:,} spots × {n_var:,} genes")
    print(f"Categorical obs: {', '.join(info['obs_categorical'])}")
    obs_num = info["obs_numeric"]
    print(f"Numeric obs (QC): {', '.join(obs_num[:8])}" + (" ..." if len(obs_num) > 8 else ""))
    print(f"Marker groups ({len(info['marker_groups'])}): {', '.join(info['marker_groups'])}")


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
