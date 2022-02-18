"""module contains pca implementation using python"""

import numpy
from scipy import stats
from sklearn.decomposition import PCA


def compute_pca(matrix):

    pca = PCA()
    scaled_data = preprocessing.scale(matrix)

    pca.fit(scaled_data)

    return {
        "pca": pca
        "components": pca_obj.components_,
        "scores": pca.transform(scaled_data)
    }


def compute_zscores(nums: list, axis: int = 0, ddof: int = 0) -> list:

    nums_array = numpy.array(nums)

    zscores = stats.zscore(nums_array, axis=axis, ddof=ddof)

    return list(zscores)
