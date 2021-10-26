"""
This module will hold generic functions that can operate on a wide-array of
data structures.
"""

from math import ceil
from functools import reduce
from typing import Any, Tuple, Sequence

def partition_all(num: int, items: Sequence[Any]) -> Tuple[Tuple[Any, ...], ...]:
    """
    Given a sequence `items`, return a new sequence of the same type as `items`
    with the data partitioned into sections of `n` items per partition.

    This is an approximation of clojure's `partition-all` function.
    """
    def __compute_start_stop__(acc, iteration):
        start = iteration * num
        return acc + ((start, start + num),)

    iterations = range(ceil(len(items) / num))
    return tuple([# type: ignore[misc]
        tuple(items[start:stop]) for start, stop # type: ignore[has-type]
        in reduce(
            __compute_start_stop__, iterations, tuple())])
