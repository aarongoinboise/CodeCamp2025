from indiv import get_indiv

def get_rbs(year):
    """
    Uses get_indiv to return rb dataframe.
    """
    return get_indiv(year, 'RB')