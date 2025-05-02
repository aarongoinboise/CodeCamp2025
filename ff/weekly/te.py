from indiv import get_indiv

def get_tes(year):
    """
    Uses get_indiv to return te dataframe.
    """
    return get_indiv(year, 'TE')