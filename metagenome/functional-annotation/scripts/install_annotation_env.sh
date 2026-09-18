#!/usr/bin/env bash
set -euo pipefail

env_name="metagenome-annotation-stack"
env_prefix=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-name) env_name="$2"; shift 2 ;;
    --env-prefix) env_prefix="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash install_annotation_env.sh [--env-name metagenome-annotation-stack] [--env-prefix /home/USER/software/conda-envs/metagenome-annotation-stack]"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

command -v conda >/dev/null 2>&1 || { echo "conda not found in PATH" >&2; exit 1; }
eval "$(conda shell.bash hook)"
if [[ -n "$env_prefix" ]]; then
  mkdir -p "$(dirname "$env_prefix")"
  conda create -y -p "$env_prefix" -c bioconda -c conda-forge -c defaults eggnog-mapper=2.1.9 diamond=2.1.6 rgi=6.0.3
  conda activate "$env_prefix"
else
  conda create -y -n "$env_name" -c bioconda -c conda-forge -c defaults eggnog-mapper=2.1.9 diamond=2.1.6 rgi=6.0.3
  conda activate "$env_name"
fi
emapper.py -h >/dev/null
diamond version >/dev/null
rgi --version >/dev/null
