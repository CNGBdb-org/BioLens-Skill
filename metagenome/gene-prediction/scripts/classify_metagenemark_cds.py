#!/usr/bin/env python3
import csv, re, sys
from pathlib import Path

if len(sys.argv) != 3:
    print("Usage: classify_metagenemark_cds.py input.gmm output.tsv", file=sys.stderr)
    sys.exit(1)

inp = Path(sys.argv[1])
out = Path(sys.argv[2])
text = inp.read_text(errors='ignore').splitlines()
rows = []
pat = re.compile(r'^(\s*\d+\s+)([<>]?)(\d+)\s+([<>]?)(\d+)\s+([+-])')
for line in text:
    m = pat.search(line)
    if not m:
        continue
    left_flag = m.group(2)
    right_flag = m.group(4)
    strand = m.group(5)
    if left_flag and right_flag:
      status = 'both-truncated'
    elif strand == '+':
      status = "5'-truncated" if left_flag else ("3'-truncated" if right_flag else 'complete')
    else:
      status = "3'-truncated" if left_flag else ("5'-truncated" if right_flag else 'complete')
    rows.append([len(rows)+1, m.group(3), m.group(5), m.group(4), strand, status])

with out.open('w', newline='') as f:
    w = csv.writer(f, delimiter='\t')
    w.writerow(['gene_id','start','end','strand','boundary_status'])
    w.writerows(rows)
