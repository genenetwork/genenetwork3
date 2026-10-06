"""module contains pca implementation using python"""


from typing import Any
from scipy import stats

import numpy as np
import redis


from typing_extensions import TypeAlias

fArray: TypeAlias = list[float] # pylint: disable=[invalid-name]


def correlation_matrix_eigendecomposition(
        corr_matrix: list[fArray]) -> tuple[np.ndarray, np.ndarray]:
    """
    decomposes a correlation matrix into eigen values and eigen vectors

    The principal components of a set of traits are the eigen vectors of
    their correlation matrix, so this is the decomposition that both the
    displayed loadings and the component scores must be built from.

    Parameters:

          corr_matrix(list[list]):a symmetric correlation matrix


    Returns:

          (eigen_values, eigen_vectors):sorted by descending eigen value,\
          with the eigen vectors held as columns


    """

    (eigen_values, eigen_vectors) = np.linalg.eigh(
        np.asarray(corr_matrix, dtype=float))

    idx = eigen_values.argsort()[::-1]
    eigen_values = eigen_values[idx]
    eigen_vectors = eigen_vectors[:, idx]

    # The sign of an eigen vector is arbitrary. Anchor each one on its
    # largest loading so that the loadings and the mapped traits keep a
    # conventional orientation, and so results do not flip between LAPACK
    # builds.
    signs = np.sign(eigen_vectors[
        np.argmax(np.abs(eigen_vectors), axis=0),
        np.arange(eigen_vectors.shape[1])])
    signs[signs == 0] = 1

    return (eigen_values, eigen_vectors * signs)


def compute_pca(array: list[fArray]) -> dict[str, Any]:
    """
    computes the principal component analysis of a correlation matrix

    Parameters:

          array(list[list]):a correlation matrix to perform pca on


    Returns:
           pca_dict(dict):dict contains the pca components and the explained\
           variance ratios


    """

    (eigen_values, eigen_vectors) = correlation_matrix_eigendecomposition(array)

    return {
        "components": eigen_vectors.T,
        "explained_variance_ratio": eigen_values / eigen_values.sum()
    }


def generate_scree_plot_data(variance_ratio: fArray) -> tuple[list, fArray]:
    """
    generates the scree data for plotting

    Parameters:

            variance_ratio(list[floats]):ratios for contribution of each pca

    Returns:

            coordinates(list[(x_coor,y_coord)])


    """

    perc_var = [round(ratio*100, 1) for ratio in variance_ratio]

    x_coordinates = [f"PC{val}" for val in range(1, len(perc_var)+1)]

    return (x_coordinates, perc_var)


def generate_pca_traits_vals(trait_data_array: list[fArray],
                             corr_array: list[fArray]) -> np.ndarray:
    """
    generates pca traits values from zscores of the traits and eigen_vectors\
    of correlation matrix

    Parameters:

            trait_data_array(list[floats]):a list of the traits
            corr_array(list[list]): list of arrays for computing eigen_vectors

    Returns:

            pca_vals(numpy.ndarray):a row per principal component and a\
            column per sample


    """

    # Standardise each trait (a row) across the samples (the columns)
    trait_zscores = stats.zscore(trait_data_array, axis=1, ddof=1)

    if len(trait_data_array[0]) < 10:
        trait_zscores = trait_data_array

    (_eigen_values, corr_eigen_vectors) = correlation_matrix_eigendecomposition(
        corr_array)

    return np.dot(corr_eigen_vectors.T, trait_zscores)


def process_factor_loadings_tdata(factor_loadings, traits_num: int):
    """

    transform loadings for tables visualization

    Parameters:
           factor_loading(numpy.ndarray)
           traits_num(int):number of traits

    Returns:
           tabular_loadings(list[list[float]])
    """

    target_columns = 3 if traits_num > 2 else 2

    trait_loadings = list(factor_loadings.T)

    return [list(trait_loading[:target_columns])
            for trait_loading in trait_loadings]


def generate_pca_temp_traits(
    species: str,
    group: str,
    traits_data: list[fArray],
    corr_array: list[fArray],
    dataset_samples: list[str],
    shared_samples: list[str],
    create_time: str
) -> dict[str, list[Any]]:
    """


    generate pca temp datasets

    """

    # pylint: disable=[too-many-arguments, too-many-positional-arguments]

    pca_trait_dict = {}

    pca_vals = generate_pca_traits_vals(traits_data, corr_array)

    for (idx, pca_trait) in enumerate(list(pca_vals)):

        trait_id = f"PCA{str(idx+1)}_{species}_{group}_{create_time}"
        sample_vals = []

        pointer = 0

        for sample in dataset_samples:
            if sample in shared_samples:

                sample_vals.append(str(pca_trait[pointer]))
                pointer += 1

            else:
                sample_vals.append("x")

        pca_trait_dict[trait_id] = sample_vals

    return pca_trait_dict


def cache_pca_dataset(redis_conn: Any, exp_days: int,
                      pca_trait_dict: dict[str, list[Any]]):
    """

    caches pca dataset to redis

    Parameters:

            redis_conn(object)
            exp_days(int): fo redis cache
            pca_trait_dict(Dict): contains traits and traits vals to cache

    Returns:

            boolean(True if correct conn object False incase of exception)


    """

    try:
        for trait_id, sample_data in pca_trait_dict.items():
            samples_str = " ".join([str(x) for x in sample_data])
            redis_conn.set(trait_id, samples_str, ex=exp_days)
        return True

    except (redis.ConnectionError, AttributeError):
        return False
