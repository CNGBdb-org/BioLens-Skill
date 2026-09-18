#!/usr/bin/env bash

set -euo pipefail

require_conda() {
  if ! command -v conda >/dev/null 2>&1; then
    echo "conda not found in PATH" >&2
    exit 1
  fi
  eval "$(conda shell.bash hook)"
}

activate_conda_env() {
  local env_name="${1:-}"
  local env_prefix="${2:-}"

  require_conda

  if [[ -n "$env_prefix" ]]; then
    if [[ ! -d "$env_prefix" ]]; then
      echo "conda env prefix not found: $env_prefix" >&2
      exit 1
    fi
    conda activate "$env_prefix"
  elif [[ -n "$env_name" ]]; then
    conda activate "$env_name"
  else
    echo "either env_name or env_prefix must be provided" >&2
    exit 1
  fi
}

ensure_command_after_activation() {
  local cmd_name="$1"
  command -v "$cmd_name" >/dev/null 2>&1 || {
    echo "$cmd_name not found after conda activation" >&2
    exit 1
  }
}

print_active_conda_env() {
  echo "CONDA_PREFIX=${CONDA_PREFIX:-NA}"
  echo "CONDA_DEFAULT_ENV=${CONDA_DEFAULT_ENV:-NA}"
}
