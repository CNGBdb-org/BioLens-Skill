#!/usr/bin/env bash
set -euo pipefail

env_name="metagenome-megahit-1.2.9"
env_prefix=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-name) env_name="$2"; shift 2 ;;
    --env-prefix) env_prefix="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash install_megahit_env.sh [--env-name metagenome-megahit-1.2.9] [--env-prefix /home/USER/software/conda-envs/metagenome-megahit-1.2.9]"
      exit 0
      ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

command -v conda >/dev/null 2>&1 || { echo "conda not found in PATH" >&2; exit 1; }
eval "$(conda shell.bash hook)"

if [[ -n "$env_prefix" ]]; then
  mkdir -p "$(dirname "$env_prefix")"
  conda create -y -p "$env_prefix" -c bioconda -c conda-forge -c defaults megahit=1.2.9
  conda activate "$env_prefix"
else
  conda create -y -n "$env_name" -c bioconda -c conda-forge -c defaults megahit=1.2.9
  conda activate "$env_name"
fi

megahit --help >/dev/null
