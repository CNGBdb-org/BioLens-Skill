#!/usr/bin/env bash
# Standalone CIMA cis-xQTL lookup (no sibling explore skill required)
# Usage:
#   ./scripts/xqtl.sh --gene CDC42 --max 20
#   ./scripts/xqtl.sh --analysis cis-caQTL --celltype Bn_TCL1A --gene CDC42

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR/_lib${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$SCRIPT_DIR/xqtl_lookup.py" "$@"
