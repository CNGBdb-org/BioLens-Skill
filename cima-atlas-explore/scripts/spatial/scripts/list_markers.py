#!/usr/bin/env python3
"""List precomputed marker genes from index.json.gz."""

import argparse
import json
import sys

from bootstrap import prepare_atlas_paths
from atlas_registry import DEFAULT_OBS_LABEL

prepare_atlas_paths()

from io_core import list_markers, load_schema, sample_name, validate_dataset_dir


def main():
    p = argparse.ArgumentParser(description="List marker genes from dataset schema.")
    p.add_argument("data_dir")
    p.add_argument("--group", "-g", default=None, help=f"Filter by marker group ({DEFAULT_OBS_LABEL})")
    p.add_argument("--celltype", "-c", default=None, help="Alias for --group")
    p.add_argument("--annotation", "-a", default=None, help="Alias for --group")
    p.add_argument("--search", "-s", default=None)
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    group = args.group or args.celltype or args.annotation
    ds = validate_dataset_dir(args.data_dir)
    schema = load_schema(ds)
    hits = list_markers(schema, celltype=group, search=args.search)

    if args.format == "json":
        print(json.dumps({"sample": sample_name(ds), "markers": hits}, indent=2, ensure_ascii=False))
        return

    print(f"Sample: {sample_name(ds)}")
    if not hits:
        print("No markers matched.")
        if group:
            names = sorted({str(m.get("name")) for m in schema.get("markers", [])})
            print(f"Available groups ({len(names)}): {', '.join(names[:30])}" + (" ..." if len(names) > 30 else ""))
        return

    for m in hits:
        feats = m.get("features", [])
        print(f"\n[{m.get('category', '')}] {m['name']}")
        print("  " + ", ".join(str(f) for f in feats))


if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
