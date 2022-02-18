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


def generate_scree_plot_data(variance_ratio):

    perc_var = np.round(variance_ratio*100, decimals=1)

    x_coordinates = [f"PC{val}" for val in range(1, len(perc_var)+1)]

    y_coordinates = np.round(pca_obj.explained_variance_ratio_*100, decimals=1)

    return list(zip(x_coordinates, y_coordinates)
