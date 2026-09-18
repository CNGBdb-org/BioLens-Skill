#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$script_dir/../../_shared/conda_env_helpers.sh"

sample_list=""
seq_dir=""
out_root=""
threads=""
conda_env_name="metagenome-fastp-0.20.1"
conda_env_prefix=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sample-list) sample_list="$2"; shift 2 ;;
    --seq-dir) seq_dir="$2"; shift 2 ;;
    --out-root) out_root="$2"; shift 2 ;;
    --threads) threads="$2"; shift 2 ;;
    --conda-env-name) conda_env_name="$2"; shift 2 ;;
    --conda-env-prefix) conda_env_prefix="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash run_fastp_qc.sh --sample-list sample.txt --seq-dir seq --out-root temp [--threads 10] [--conda-env-name metagenome-fastp-0.20.1] [--conda-env-prefix /home/USER/software/conda-envs/metagenome-fastp-0.20.1]"
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

[[ -n "$sample_list" ]] || { echo "--sample-list is required" >&2; exit 1; }
[[ -n "$seq_dir" ]] || { echo "--seq-dir is required" >&2; exit 1; }
[[ -n "$out_root" ]] || { echo "--out-root is required" >&2; exit 1; }
[[ -f "$sample_list" ]] || { echo "sample list not found: $sample_list" >&2; exit 1; }

activate_conda_env "$conda_env_name" "$conda_env_prefix"
ensure_command_after_activation fastp
print_active_conda_env
fastp --version

while IFS= read -r sample || [[ -n "$sample" ]]; do
  [[ -n "$sample" ]] || continue
  mkdir -p "$out_root/$sample/fastp"
  r1="$seq_dir/$sample/${sample}_1.fastq.gz"
  r2="$seq_dir/$sample/${sample}_2.fastq.gz"
  [[ -f "$r1" ]] || { echo "missing input: $r1" >&2; exit 1; }
  [[ -f "$r2" ]] || { echo "missing input: $r2" >&2; exit 1; }

  cmd=(fastp -i "$r1" -o "$out_root/$sample/fastp/${sample}_clean_1.fq.gz" -I "$r2" -O "$out_root/$sample/fastp/${sample}_clean_2.fq.gz" --json "$out_root/$sample/fastp/${sample}_fastp.json" --html "$out_root/$sample/fastp/${sample}_fastp.html")
  if [[ -n "$threads" ]]; then
    cmd+=(--thread "$threads")
  fi
  "${cmd[@]}"
done < "$sample_list"

echo "fastp QC completed"
