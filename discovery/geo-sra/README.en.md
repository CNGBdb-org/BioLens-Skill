# GEO / SRA / BioProject

NCBI **GEO**, **SRA**, and **BioProject** discovery skill for **single-cell / spatial** public datasets. Finds GSE/GSM accessions, processed matrix FTP links, BioProject/SRA identifiers, and controlled-access notes (EGA/dbGaP). **Does not** run clustering or annotation.

```bash
cd skills/discovery/geo-sra
python ./scripts/query.py search "liver"
python ./scripts/query.py gse GSE149614
python ./scripts/query.py resolve GSE149614
```

Requires: `pip install -r ../../requirements.txt`. Optional: `NCBI_API_KEY`.
