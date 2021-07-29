"""
DESCRIPTION:
    TODO: Add a description for the module

FUNCTIONS:
slink:
    TODO: Describe what the function does...
"""
import logging
from typing import List, Tuple, Union, Sequence

NumType = Union[int, float]
SeqOfNums = Sequence[NumType]

class LengthError(BaseException):
    """Raised whenever child lists/tuples are not the same length as the parent
    list of tuple."""

class MirrorError(BaseException):
    """Raised if the distance from child A to child B is not the same as the
    distance from child B to child A."""

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
    inner_coords = range(len(lists))
    coords = ((i, j) for i in inner_coords for j in inner_coords)
    def __is_same_reversed(coord):
        return lists[coord[0]][coord[1]] == lists[coord[1]][coord[0]]
    if not all(map(__is_same_reversed, coords)):
        raise MirrorError((
            "Distance from one child to the other should be the same in both "
            "directions."))

def __raise_valueerror_on_negative_distances(lists):
    """Check that distances between 'somethings' are all positive, otherwise,
raise an exception."""
    def zero_or_positive(val):
        return val >= 0
    # flatten lists
    flattened = __flatten_list_of_lists(lists)
    if not all(map(zero_or_positive, flattened)):
        raise ValueError("Distances should be positive.")

def __flatten_list_of_lists(parent):
    return [item for child in parent for item in child]

# i and j are Union[SeqOfNums, NumType], but that leads to errors where the
# values of i or j are indexed, since the NumType type is not indexable.
# I don't know how to type this so that it does not fail on running `mypy .`
def nearest(lists: Sequence[SeqOfNums], i, j) -> NumType:
    """
    Computes shortest distance between member(s) in `i` and member(s) in `j`.

    Description:
    This is 'copied' over from genenetwork1, from
    https://github.com/genenetwork/genenetwork1/blob/master/web/webqtl/heatmap/slink.py#L42-L64.

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
    if isinstance(i, int) and isinstance(j, int): # From member i to member j
        return lists[i][j]

    if isinstance(i, int) and __is_list_or_tuple(j):
        return min(map(lambda j_new: nearest(lists, i, j_new), j[:-1]))
    if isinstance(j, int) and __is_list_or_tuple(i):
        return min(map(lambda i_new: nearest(lists, i_new, j), i[:-1]))

    if __is_list_or_tuple(i) and __is_list_or_tuple(j):
        coordinate_pairs = __flatten_list_of_lists(
            [[(itemi, itemj) for itemj in j[:-1]] for itemi in i[:-1]])
        return min(map(lambda x: nearest(lists, x[0], x[1]), coordinate_pairs))

    raise ValueError("member values (i or j) should be lists/tuples of integers or integers")

# `lists` here could be Sequence[SeqOfNums], but that leads to errors I do not
# understand down the line
# Might have to re-implement the function especially since the errors are thrown
# where `listindexcopy` is involved
def slink(lists):
    """
    DESCRIPTION:
    TODO: Not quite sure what this function does. Work through the code with a
        fine tooth comb, once we understand the context of its use, so as to
        give a better description

        The name of the function does not clearly establish what the function
        does either, meaning, once that is established, the function should be
        renamed to give the user an idea of what it does without necessarily
        reading through a ton of code.

        We should also look into refactoring the function to reduce/eliminate
        the multiple levels of nested-loops and conditionals

    PARAMETERS:
    lists (list of lists of numbers): Give this a better name.
        Each item of this list is a list of coordinates of the members in the
        group.
        What 'member' and 'group' in this context means, is not yet established.
    """
    try:
        size = len(lists)
        listindexcopy = list(range(size))
        listscopy = [child[:] for child in lists]
        init_size = size
        candidate = []
        while init_size > 2:
            mindist = 1e10
            for i in range(init_size):
                for j in range(i+1, init_size):
                    if listscopy[i][j] < mindist:
                        mindist = listscopy[i][j]
                        candidate = [[i, j]]
                    elif listscopy[i][j] == mindist:
                        mindist = listscopy[i][j]
                        candidate.append([i, j])
                    else:
                        pass
            newmem = (
                listindexcopy[candidate[0][0]], listindexcopy[candidate[0][1]],
                mindist)
            listindexcopy.pop(candidate[0][1])
            listindexcopy[candidate[0][0]] = newmem

            init_size -= 1
            for i in range(init_size):
                for j in range(i+1, init_size):
                    listscopy[i][j] = nearest(
                        lists, listindexcopy[i], listindexcopy[j])
                    listscopy[j][i] = listscopy[i][j]
        listindexcopy.append(
            nearest(lists, listindexcopy[0], listindexcopy[1]))
        return listindexcopy
    except (LengthError, MirrorError, TypeError, IndexError) as exc:
        # Look into making the logging log output to the system's
        #   configured logger(s)
        logging.warning("Exception: %s, %s", type(exc), exc)
        return []
