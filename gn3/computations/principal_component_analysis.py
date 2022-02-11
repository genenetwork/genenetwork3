"""module contains pca implementation using python"""

import numpy
from scipy import stats


def compute_zscores(nums: list, axis: int = 0, ddof: int = 0) -> list:

    nums_array = numpy.array(nums)

    zscores = stats.zscore(nums_array, axis=axis, ddof=ddof)

    return list(zscores)
