#!/usr/bin/env bash
# Standalone CIMA SMR lookup (no sibling explore skill required)
# Usage:
#   ./scripts/smr.sh --gene CTLA4 --max 10
#   ./scripts/smr.sh --gene BLK --trait RA --max 10
#   ./scripts/smr.sh --source caqtl --gene ARL14EP --max 10

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export PYTHONPATH="$SCRIPT_DIR/_lib${PYTHONPATH:+:$PYTHONPATH}"
exec python3 "$SCRIPT_DIR/smr_lookup.py" "$@"
