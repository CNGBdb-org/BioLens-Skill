#!/usr/bin/env bash
set -euo pipefail

blast_env_name="metagenome-blast-2.16.0"
blast_env_prefix=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --blast-env-name) blast_env_name="$2"; shift 2 ;;
    --blast-env-prefix) blast_env_prefix="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash install_structure_env.sh [--blast-env-name metagenome-blast-2.16.0] [--blast-env-prefix /home/USER/software/conda-envs/metagenome-blast-2.16.0]"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done
command -v conda >/dev/null 2>&1 || { echo "conda not found in PATH" >&2; exit 1; }
eval "$(conda shell.bash hook)"
if [[ -n "$blast_env_prefix" ]]; then
  mkdir -p "$(dirname "$blast_env_prefix")"
  conda create -y -p "$blast_env_prefix" -c bioconda -c conda-forge -c defaults blast=2.16.0
  conda activate "$blast_env_prefix"
else
  conda create -y -n "$blast_env_name" -c bioconda -c conda-forge -c defaults blast=2.16.0
  conda activate "$blast_env_name"
fi
blastp -version >/dev/null
