"""
DESCRIPTION:
    TODO: Add a description for the module

FUNCTIONS:
slink:
    TODO: Describe what the function does...
"""
import logging
from functools import partial

class LengthError(BaseException):
    pass

class MirrorError(BaseException):
    pass

def __is_list_or_tuple(item):
    return type(item) in [list, tuple]

def __raise_valueerror_if_data_is_not_lists_or_tuples(lists):
    """Check that `lists` is a list of lists: If not, raise an exception."""

    if (not __is_list_or_tuple(lists)) or (not all(map(__is_list_or_tuple, lists))):
        raise ValueError("Expected list or tuple")

def __raise_valueerror_if_lists_empty(lists):
    """Check that the list and its direct children are not empty."""
    def empty(lst):
        return len(lst) == 0
    if (empty(lists)) or not all(map(lambda x: not empty(x), lists)):
        raise ValueError("List/Tuple should NOT be empty!")

def __raise_lengtherror_if_child_lists_are_not_same_as_parent(lists):
    def len_is_same_as_parent(lst):
        return len(lst) == len(lists)
    if not all(map(len_is_same_as_parent, lists)):
        raise LengthError("All children lists should be same length as the parent.")

def __raise_valueerror_if_child_list_distance_from_itself_is_not_zero(lists):
    def get_child_distance(child):
        idx = lists.index(child)
        return lists[idx][idx]
    def distance_is_zero(dist):
        return dist == 0
    children_distances = map(get_child_distance, lists)
    if not all(map(distance_is_zero, children_distances)):
        raise ValueError("Distance of each child list/tuple from itself should be zero!")

def __raise_mirrorerror_of_distances_one_way_are_not_same_other_way(lists):
    """Check that the distance from A to B, is the same as the distance from B to A.
If the two distances are different, throw an exception."""
    for i in range(len(lists)):
        for j in range(len(lists)):
            if lists[i][j] != lists[j][i]:
                raise MirrorError(
                    ("Distance from one child({}) to the other ({}) "
                     "should be the same in both directions.").format(
                         lists[i][j], lists[j][i]))

def __raise_valueerror_on_negative_distances(lists):
    """Check that distances between 'somethings' are all positive, otherwise,
raise an exception."""
    def zero_or_positive(val):
        return val >= 0;
    # flatten lists
    flattened = [distance for child in lists for distance in child]
    if not all(map(zero_or_positive, flattened)):
        raise ValueError("Distances should be positive.")

def nearest(lists, i, j):
    """
    Computes shortest distance between member(s) in `i` and member(s) in `j`.

    Description:
    This is 'copied' over from genenetwork1, from https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/heatmap/slink.py#L42-L64.

    This description should be updated to better describe what 'member' means in
    the context where the function is used.

    Parameters:
    lists (list of lists of distances): Represents a list of members and their
        distances from each other.
        Each inner list represents the distances the member at that coordinate
        is from other members in the list: for example, a member at index 0 with
        the values [0, 9, 1, 7] indicates that the member is:
        - 0 units of distance away from itself
        - 9 units of distance away from member at coordinate 1
        - 1 unit of distance away from member at coordinate 2
        - 7 units of distance away from member at coordinate 3
    i (int or list of ints): Represents the coordinate of a member, or a list of
        coordinates of members on the `lists` list.
    j (int or list of ints): Represents the coordinate of a member, or a list of
        coordinates of members on the `lists` list.

    Returns:
    int: Represents the shortest distance between member(s) in `i` and member(s)
        in `j`."""

    #### Guard Functions: Should we do this a different way? ####
    __raise_valueerror_if_data_is_not_lists_or_tuples(lists)
    __raise_valueerror_if_lists_empty(lists)
    __raise_lengtherror_if_child_lists_are_not_same_as_parent(lists)
    __raise_valueerror_if_child_list_distance_from_itself_is_not_zero(lists)
    __raise_mirrorerror_of_distances_one_way_are_not_same_other_way(lists)
    __raise_valueerror_on_negative_distances(lists)
    #### END: Guard Functions ####
    if type(i) == int and type(j) == int: # From member i to member j
        return lists[i][j]
    elif type(i) == int and __is_list_or_tuple(j):
        return min(map(lambda j_new: nearest(lists, i, j_new), j[:-1]))
    elif type(j) == int and __is_list_or_tuple(i):
        return min(map(lambda i_new: nearest(lists, i_new, j), i[:-1]))
    elif __is_list_or_tuple(i) and __is_list_or_tuple(j):
        partial_i = map(lambda x:partial(nearest, lists, x), i[:-1])
        ns = list(map(lambda f, x: f(x), partial_i, j[:1]))
        return min(ns)
    else:
        raise ValueError("member values (i or j) should be lists/tuples of integers or integers")

def slink(lists):
    """
    """
    try:
        nearest(lists, 1, 2)
    except Exception as e:
        # TODO: Look into making the logging log output to the system's
        #    configured logger(s)
        logging.warning("Exception: {}, {}".format(type(e), e))
        return []
