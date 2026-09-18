"""Paper / virus / disease gene tables per atlas."""

from atlas_registry import get_atlas


def _tables():
    name = get_atlas().name
    if name == "hesta":
        from gene_tables import DISEASE_CATEGORIES, PAPER_PANELS, VIRUS_RECEPTORS
    elif name == "mccsta":
        from mccsta_gene_tables import DISEASE_CATEGORIES, PAPER_PANELS, VIRUS_RECEPTORS
    elif name == "cima":
        from cima_gene_tables import DISEASE_CATEGORIES, PAPER_PANELS, VIRUS_RECEPTORS
    else:
        from mosta_gene_tables import DISEASE_CATEGORIES, PAPER_PANELS, VIRUS_RECEPTORS
    return PAPER_PANELS, VIRUS_RECEPTORS, DISEASE_CATEGORIES


def paper_panels():
    return _tables()[0]


def virus_receptors():
    return _tables()[1]


def disease_categories():
    return _tables()[2]
