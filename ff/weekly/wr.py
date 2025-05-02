from indiv import get_indiv

def get_wrs(year):
    """
    Uses get_indiv to return wr dataframe.
    """
    return get_indiv(year, 'WR')