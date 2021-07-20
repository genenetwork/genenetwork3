from math import sqrt
from functools import reduce
## From GN1: mostly for clustering and heatmap generation

def items_with_values(dbdata, userdata):
    """Retains only corresponding items in the data items that are not `None` values.
This should probably be renamed to something sensible"""
    def both_not_none(item1, item2):
        if (item1 is not None) and (item2 is not None):
            return (item1, item2)
        return None
    def split_lists(accumulator, item):
        return [accumulator[0] + [item[0]], accumulator[1] + [item[1]]]
    return reduce(
        split_lists,
        filter(lambda x: x is not None, map(both_not_none, dbdata, userdata)),
        [[], []])

def compute_correlation(dbdata, userdata):
    x, y = items_with_values(dbdata, userdata)
    if len(x) < 6:
        return (0.0, len(x))
    meanx = sum(x)/len(x)
    meany = sum(y)/len(y)
    def cal_corr_vals(acc, item):
        xitem, yitem = item
        return [
            acc[0] + ((xitem - meanx) * (yitem - meany)),
            acc[1] + ((xitem - meanx) * (xitem - meanx)),
            acc[2] + ((yitem - meany) * (yitem - meany))]
    xyd, sxd, syd = reduce(cal_corr_vals, zip(x, y), [0.0, 0.0, 0.0])
    try:
        return ((xyd/(sqrt(sxd)*sqrt(syd))), len(x))
    except ZeroDivisionError as zde:
        return(0, len(x))
