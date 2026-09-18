#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

sample_list=""
temp_root=""
metagenemark_bin=""
model_file=""
codon_table="11"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sample-list) sample_list="$2"; shift 2 ;;
    --temp-root) temp_root="$2"; shift 2 ;;
    --metagenemark-bin) metagenemark_bin="$2"; shift 2 ;;
    --model-file) model_file="$2"; shift 2 ;;
    --codon-table) codon_table="$2"; shift 2 ;;
    -h|--help)
      echo "Usage: bash run_metagenemark_prediction.sh --sample-list sample.txt --temp-root temp --metagenemark-bin /path/gmhmmp --model-file /path/MetaGeneMark_v1.mod [--codon-table 11]"
      exit 0 ;;
    *) echo "Unknown argument: $1" >&2; exit 1 ;;
  esac
done

[[ -f "$sample_list" ]] || { echo "sample list not found: $sample_list" >&2; exit 1; }
[[ -x "$metagenemark_bin" ]] || { echo "MetaGeneMark binary not executable: $metagenemark_bin" >&2; exit 1; }
[[ -f "$model_file" ]] || { echo "model file not found: $model_file" >&2; exit 1; }

while IFS= read -r sample || [[ -n "$sample" ]]; do
  [[ -n "$sample" ]] || continue
  contigs="$temp_root/$sample/assembly/${sample}.contigs.fa"
  outdir="$temp_root/$sample/metagenemark"
  mkdir -p "$outdir"
  [[ -f "$contigs" ]] || { echo "missing contigs: $contigs" >&2; exit 1; }

  "$metagenemark_bin" -m "$model_file" -o "$outdir/${sample}.gmm" "$contigs" -A "$outdir/${sample}_prot.fa"
  python3 "$script_dir/classify_metagenemark_cds.py" "$outdir/${sample}.gmm" "$outdir/${sample}_cds_status.tsv"
  cp "$outdir/${sample}_prot.fa" "$outdir/${sample}_complete_prot.fa"
  echo "sample=$sample codon_table=$codon_table" > "$outdir/${sample}_translation_meta.txt"
done < "$sample_list"

echo "MetaGeneMark prediction completed"
