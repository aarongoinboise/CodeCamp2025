from indiv import get_indiv

def get_qbs(year):
    """
    Uses get_indiv to return qb dataframe.
    """
    return get_indiv(year, 'QB')