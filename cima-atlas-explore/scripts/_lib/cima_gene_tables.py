"""Curated CIMA gene panels (Science 2026 / TrueBlood)."""

PAPER = {
    "title": "Chinese Immune Multi-Omics Atlas",
    "journal": "Science",
    "doi": "10.1126/science.adt3130",
    "portal": "https://db.cngb.org/trueblood/cima/",
}

PAPER_PANELS = {
    "b_lineage": {
        "title": "B cell lineage markers",
        "genes": ["MS4A1", "CD79A", "CD19", "CD27", "IGHM", "IGHG1", "MZB1", "XBP1"],
        "default_sample": "B",
    },
    "cd4t": {
        "title": "CD4+ T cell markers",
        "genes": ["CD4", "IL7R", "CCR7", "FOXP3", "GZMK", "CXCR5", "IFNG", "CTLA4"],
        "default_sample": "CD4T",
    },
    "cd8t": {
        "title": "CD8+ T cell markers",
        "genes": ["CD8A", "CD8B", "GZMB", "GZMH", "PRF1", "NKG7", "TCF7", "PDCD1"],
        "default_sample": "CD8T",
    },
    "nk": {
        "title": "NK cell markers",
        "genes": ["NCAM1", "KLRD1", "NKG7", "GNLY", "PRF1", "FCGR3A", "XCL1", "GZMB"],
        "default_sample": "NK",
    },
    "myeloid": {
        "title": "Myeloid / DC markers",
        "genes": ["LYZ", "S100A8", "FCN1", "CD14", "CD1C", "CLEC9A", "IRF8", "HLA-DRA"],
        "default_sample": "Myeloid",
    },
    "pbmc_overview": {
        "title": "Major PBMC lineages",
        "genes": ["CD3D", "CD4", "CD8A", "MS4A1", "NKG7", "LYZ", "FCGR3A", "HBB"],
        "default_sample": "PBMCs",
    },
    "age_immune": {
        "title": "Age-associated immune genes (literature + CIMA DC2)",
        "genes": ["IKZF4", "IL12B", "CXCL8", "CCL2", "HLA-DRA", "CD74", "FCER1A", "TLR7"],
        "default_sample": "Myeloid",
    },
}

IMMUNE_DISEASE_GENES = {
    "autoimmune": {
        "title": "Autoimmune / inflammation (SMR examples from CIMA)",
        "genes": ["IKZF4", "IL12B", "PTPN22", "STAT4", "TNFAIP3", "CD40", "IRF5"],
    },
    "asthma_allergy": {
        "title": "Asthma / allergy",
        "genes": ["IKZF4", "IL33", "GATA3", "IL13", "IL4R", "TSLP", "HLA-DQB1"],
    },
    "metabolic": {
        "title": "Metabolic / lipid (CIMA in-house GWAS traits)",
        "genes": ["APOE", "LDLR", "PCSK9", "GCKR", "FADS1", "CETP", "LPL"],
    },
}

VIRUS_RECEPTORS = {}
DISEASE_CATEGORIES = IMMUNE_DISEASE_GENES
