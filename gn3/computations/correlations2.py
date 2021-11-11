"""
DESCRIPTION:
    TODO: Add a description for the module

FUNCTIONS:
compute_correlation:
    TODO: Describe what the function does..."""

from math import sqrt
## From GN1: mostly for clustering and heatmap generation

def __items_with_values(dbdata, userdata):
    """Retains only corresponding items in the data items that are not `None` values.
    This should probably be renamed to something sensible"""
    filtered = [x for x in zip(dbdata, userdata) if x[0] is not None and x[1] is not None]
    return tuple(zip(*filtered)) if filtered else ([], [])

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
