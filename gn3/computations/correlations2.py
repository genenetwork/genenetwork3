"""
DESCRIPTION:
    TODO: Add a description for the module

FUNCTIONS:
compute_correlation:
    TODO: Describe what the function does..."""

from scipy import stats
## From GN1: mostly for clustering and heatmap generation

def __items_with_values(dbdata, userdata):
    """Retains only corresponding items in the data items that are not `None` values.
    This should probably be renamed to something sensible"""
    filtered = [x for x in zip(dbdata, userdata) if x[0] is not None and x[1] is not None]
    return tuple(zip(*filtered)) if filtered else ([], [])

def compute_correlation(dbdata, userdata):
    """Compute the Pearson correlation coefficient.

    This is extracted from
    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/utility/webqtlUtil.py#L622-L647
    """
    x_items, y_items = __items_with_values(dbdata, userdata)
    correlation = stats.pearsonr(x_items, y_items)[0] if len(x_items) >= 6 else 0
    return (correlation, len(x_items))
