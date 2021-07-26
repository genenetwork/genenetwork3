"""
DESCRIPTION:
    TODO: Add a description for the module

FUNCTIONS:
compute_correlation:
    TODO: Describe what the function does..."""

from math import sqrt
from functools import reduce
## From GN1: mostly for clustering and heatmap generation

def __items_with_values(dbdata, userdata):
    """Retains only corresponding items in the data items that are not `None` values.
    This should probably be renamed to something sensible"""
    def both_not_none(item1, item2):
        """Check that both items are not the value `None`."""
        if (item1 is not None) and (item2 is not None):
            return (item1, item2)
        return None
    def split_lists(accumulator, item):
        """Separate the 'x' and 'y' items."""
        return [accumulator[0] + [item[0]], accumulator[1] + [item[1]]]
    return reduce(
        split_lists,
        filter(lambda x: x is not None, map(both_not_none, dbdata, userdata)),
        [[], []])

def compute_correlation(dbdata, userdata):
    """Compute some form of correlation.

    This is extracted from
    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/utility/webqtlUtil.py#L622-L647
    """
    x_items, y_items = __items_with_values(dbdata, userdata)
    if len(x_items) < 6:
        return (0.0, len(x_items))
    meanx = sum(x_items)/len(x_items)
    meany = sum(y_items)/len(y_items)
    def cal_corr_vals(acc, item):
        xitem, yitem = item
        return [
            acc[0] + ((xitem - meanx) * (yitem - meany)),
            acc[1] + ((xitem - meanx) * (xitem - meanx)),
            acc[2] + ((yitem - meany) * (yitem - meany))]
    xyd, sxd, syd = reduce(cal_corr_vals, zip(x_items, y_items), [0.0, 0.0, 0.0])
    try:
        return ((xyd/(sqrt(sxd)*sqrt(syd))), len(x_items))
    except ZeroDivisionError:
        return(0, len(x_items))
