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

def raise_lengtherror_if_child_lists_are_not_same_as_parent(lists):
    def len_is_same_as_parent(lst):
        return len(lst) == len(lists)
    if not all(map(len_is_same_as_parent, lists)):
        raise LengthError("All children lists should be same length as the parent.")

def raise_valueerror_if_child_list_distance_from_itself_is_not_zero(lists):
    def get_child_distance(child):
        idx = lists.index(child)
        return lists[idx][idx]
    def distance_is_zero(dist):
        return dist == 0
    children_distances = map(get_child_distance, lists)
    if not all(map(distance_is_zero, children_distances)):
        raise ValueError("Distance of each child list/tuple from itself should be zero!")

def raise_mirrorerror_of_distances_one_way_are_not_same_other_way(lists):
    """Check that the distance from A to B, is the same as the distance from B to A.
If the two distances are different, throw an exception."""
    for i in range(len(lists)):
        for j in range(len(lists)):
            if lists[i][j] != lists[j][i]:
                raise MirrorError(
                    ("Distance from one child({}) to the other ({}) "
                     "should be the same in both directions.").format(
                         lists[i][j], lists[j][i]))

def nearest(lists, i, j):
    """Computes some form of distance.
This is 'copied' over from genenetwork1, from https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/heatmap/slink.py#L42-L64.

This description should be updated once the form/type of 'distance' identified."""

    #### Guard Functions: Should we do this a different way? ####
    raise_valueerror_if_data_is_not_lists_or_tuples(lists)
    raise_valueerror_if_lists_empty(lists)
    raise_lengtherror_if_child_lists_are_not_same_as_parent(lists)
    raise_valueerror_if_child_list_distance_from_itself_is_not_zero(lists)
    raise_mirrorerror_of_distances_one_way_are_not_same_other_way(lists)
    #### END: Guard Functions ####
    return None
