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


def generate_scree_plot_data(variance_ratio):

    perc_var = np.round(variance_ratio*100, decimals=1)

    x_coordinates = [f"PC{val}" for val in range(1, len(perc_var)+1)]

    y_coordinates = np.round(pca_obj.explained_variance_ratio_*100, decimals=1)

    return list(zip(x_coordinates, y_coordinates))


def generate_pca_traits_data(trait_data_array: list, corr_matrix):
    """function generates new pca traits data from
    zscores and eigen vectors"""

    (corr_eigen_vectors, _eigen_values) = np.linalg.eig(np.array(trait_data_array))

    # sort the above

    trait_zscores = stats.zscore(trait_data_array)

    pca_traits_values = np.dot(corr_eigen_vectors, trait_zscores)

    return pca_trait_values
