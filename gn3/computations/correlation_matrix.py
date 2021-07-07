"""module contains code for computing pca using sklearn"""

import numpy as np
from numpy import linalg

from sklearn.decomposition import PCA
from sklearn import preprocessing

import scipy.stats as stats


def compute_the_pca(data, transform: bool = True):
    """function to compute pca"""

    pca = PCA()

    if transform is True:
        # transform the matrix
        # e.g where samples are columns and traits are rows
        scaled_data = preprocessing.scale(data.T)

    else:
        scaled_data = preprocessing.scale(data)

    # compute loading score and variaton of each pc

    # generate coordinates for pca graph if needd
    pca.fit(scaled_data)

    pca_data = pca.transform(scaled_data)

    return (pca, pca_data)


def compute_pca2(matrix):
    """compute the pca"""

    pca = PCA()
    scaled_data = preprocessing.scale(matrix)
    pca.fit(scaled_data)
    # generate coordinates

    pca_data = pca.transform(scaled_data)

    perc_var = np.round(pca.explained_variance_ratio_*100, decimals=1)
    _labels = ["PC" + str(x) for x in range(1, len(perc_var)+1)]
    return (pca, pca_data)


def compute_zscores(trait_data_arrays):
    """compute zscores of trait data arrays"""
    data = np.array(trait_data_arrays)

    zscores = stats.zscore(data, axis=1)

    return zscores


def compute_eigens(matrix):
    """compute eigen values and vectors sort by eigen values"""
    eigen_values, eigen_vectors = linalg.eig(matrix)

    idx = eigen_values.argsort()[::-1]
    eigen_values = eigen_values[idx]

    eigen_vectors = eigen_vectors[:, idx]

    return (eigen_values, eigen_vectors)
