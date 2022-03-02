"""module contains pca implementation using python"""


from typing import Any
from scipy import stats

from sklearn.decomposition import PCA
from sklearn import preprocessing

import numpy as np


from typing_extensions import TypeAlias

fArray: TypeAlias = list[float]


def compute_pca(array: list[fArray]) -> dict[str, Any]:
    """
    computes the principal component analysis

    Parameters:

          array(list[list]):a list of lists contains data to perform  pca


    Returns:
           pca_dict(dict):dict contains the pca_object,pca components,pca scores


    """

    corr_matrix = np.matrix(array)

    pca_obj = PCA()
    scaled_data = preprocessing.scale(corr_matrix)

    pca_obj.fit(scaled_data)

    return {
        "pca": pca_obj,
        "components": pca_obj.components_,
        "scores": pca_obj.transform(scaled_data)
    }


def generate_scree_plot_data(variance_ratio: fArray) -> list[tuple[str, float]]:
    """
    generates the scree data for plotting

    Parameters:

            variance_ratio(list[floats]):ratios for contribution of each pca

    Returns:

            coordinates(list[(x_coor,y_coord)])


    """

    perc_var = [round(ratio*100, 1) for ratio in variance_ratio]

    # perc_var = np.round(variance_ratio*100, decimals=1)

    x_coordinates = [f"PC{val}" for val in range(1, len(perc_var)+1)]

    return list(zip(x_coordinates, perc_var))


def generate_pca_traits_vals(trait_data_array: list[fArray],
                             corr_array: list[fArray]) -> list[list[Any]]:
    """

    generates datasets from zscores of the traits and eigen_vectors 
    of correlation matrix

    Parameters:

            trait_data_array(list[floats]):an list of the traits
            corr_array(list[list]): list of arrays for computing eigen_vectors

    Returns:

            pca_vals[list[list]]:


    """

    # sort the eigens ?/ add regression tests gn2
    trait_zscores = stats.zscore(trait_data_array)

    if len(trait_data_array[0]) < 10:
        trait_zscores = trait_data_array

    (eigen_values, corr_eigen_vectors) = np.linalg.eig(np.array(corr_array))
    idx = eigen_values.argsort()[::-1]

    return np.dot(corr_eigen_vectors[:, idx], trait_zscores)


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


def generate_pca_temp_dataset(species: str, group: str,
                              traits_data: list[fArray], corr_array: list[fArray],
                              dataset_samples: list[str], shared_samples: list[str],
                              create_time: str) -> dict[str, list[Any]]:
    """

    generate pca temp datasets

    """

    pca_trait_dict = {}

    pca_vals = generate_pca_traits_vals(traits_data, corr_array).tolist()

    for (idx, pca_trait) in enumerate(pca_vals):

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
            pca_trait_dict(Dict):contains traits and traits vals to cache

    Returns:

            boolean(True)


    """

    for trait_id, trait_sample_data in pca_trait_dict.items():

        samples_str = " ".join([str(x) for x in trait_sample_data])
        redis_conn.set(trait_id, samples_str, ex=exp_days)

    return True
