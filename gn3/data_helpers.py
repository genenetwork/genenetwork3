"""
This module will hold generic functions that can operate on a wide-array of
data structures.
"""

from math import ceil
from functools import reduce
from typing import Any, Tuple, Sequence, Optional

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

def partition_by(partition_fn, items):
    """
    Given a sequence `items`, return a tuple of tuples, each of which contain
    the values in `items` partitioned such that the first item in each internal
    tuple, when passed to `partition_function` returns True.

    This is an approximation of Clojure's `partition-by` function.
    """
    def __partitioner__(accumulator, item):
        if partition_fn(item):
            return accumulator + ((item,),)
        return accumulator[:-1] + (accumulator[-1] + (item,),)

    return reduce(__partitioner__, items, tuple())

def parse_csv_line(
        line: str, delimiter: str = ",",
        quoting: Optional[str] = '"') -> Tuple[str, ...]:
    """
    Parses a line from a CSV file into a tuple of strings.

    This is a migration of the `web.webqtl.utility.webqtlUtil.readLineCSV`
    function in GeneNetwork1.
    """
    return tuple(
        col.strip("{} \t\n".format(quoting)) for col in line.split(delimiter))
