class LengthError(BaseException):
    pass

class MirrorError(BaseException):
    pass

def raise_valueerror_if_data_is_not_lists_or_tuples(lists):
    """Check that `lists` is a list of lists: If not, raise an exception."""
    def is_list_or_tuple(item):
        return type(item) == type([]) or type(item) == type(tuple)

    if (not is_list_or_tuple(lists)) or (not all(map(is_list_or_tuple, lists))):
        raise ValueError("Expected list or tuple")

def raise_valueerror_if_lists_empty(lists):
    """Check that the list and its direct children are not empty."""
    def empty(lst):
        return len(lst) == 0
    if (empty(lists)) or not all(map(lambda x: not empty(x), lists)):
        raise ValueError("List/Tuple should NOT be empty!")

def nearest(lists, i, j):
    """Computes some form of distance.
This is 'copied' over from genenetwork1, from https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/heatmap/slink.py#L42-L64.

This description should be updated once the form/type of 'distance' identified."""

    #### Guard Functions: Should we do this a different way? ####
    raise_valueerror_if_data_is_not_lists_or_tuples(lists)
    raise_valueerror_if_lists_empty(lists)
    #### END: Guard Functions ####
    return None
