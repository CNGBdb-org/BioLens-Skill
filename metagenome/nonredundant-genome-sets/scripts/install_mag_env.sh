#!/usr/bin/env bash
set -euo pipefail

env_name="metagenome-mag-stack"
env_prefix=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-name) env_name="$2"; shift 2 ;;
    --env-prefix) env_prefix="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash install_mag_env.sh [--env-name metagenome-mag-stack] [--env-prefix /home/USER/software/conda-envs/metagenome-mag-stack]"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done
command -v conda >/dev/null 2>&1 || { echo "conda not found in PATH" >&2; exit 1; }
eval "$(conda shell.bash hook)"
if [[ -n "$env_prefix" ]]; then
  mkdir -p "$(dirname "$env_prefix")"
  conda create -y -p "$env_prefix" -c bioconda -c conda-forge -c defaults drep=3.3.0 gtdbtk=2.3.2 prodigal=2.6.3 diamond=2.1.6
  conda activate "$env_prefix"
else
  conda create -y -n "$env_name" -c bioconda -c conda-forge -c defaults drep=3.3.0 gtdbtk=2.3.2 prodigal=2.6.3 diamond=2.1.6
  conda activate "$env_name"
fi
dRep -h >/dev/null
gtdbtk -h >/dev/null
prodigal -h >/dev/null
diamond version >/dev/null
