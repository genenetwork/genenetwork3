"""module contains code for computing pca using sklearn"""

import datetime
from typing import List
from typing import Tuple

import numpy as np
from numpy import linalg

from sklearn.decomposition import PCA
from sklearn import preprocessing

import scipy.stats as stats

from gn3.computations.correlations import compute_corr_coeff_p_value
from gn3.computations.correlations import normalize_values


def compute_the_pca(data, transform: bool = True):
    """function to compute pca"""
    pca = PCA()
    if transform is True:
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

    pca_data = pca.transform(scaled_data)

    perc_var = np.round(pca.explained_variance_ratio_*100, decimals=1)
    _labels = ["PC" + str(x) for x in range(1, len(perc_var)+1)]
    return (pca, pca_data)


def compute_zscores(trait_data_arrays):
    """compute zscores of trait data arrays"""
    data = np.array(trait_data_arrays)

    zscores = stats.zscore(data, axis=1)

    return zscores


def compute_sort_eigens(matrix):
    """compute eigen values and vectors sort by eigen values"""

    eigen_values, eigen_vectors = linalg.eig(matrix)

    idx = eigen_values.argsort()[::-1]
    eigen_values = eigen_values[idx]

    eigen_vectors = eigen_vectors[:, idx]
    return (eigen_values, eigen_vectors)


def get_scree_plot_data(pca_obj):
    """get scree plot data for generating plot x=x_vals,y = perc_var"""

    perc_var = np.round(pca_obj.explained_variance_ratio_*100, decimals=1)
    x_vals = list(range(1, len(perc_var)+1))

    return {

        "x_vals": x_vals,
        "y_vals": perc_var
    }


def process_factor_loadings(pca_obj, trait_list):
    """
    fetch loading for each trait i.e
    trait_a:pca_1_load,pca_2_load ... ,
    trait_b:......
    """

    loadings = pca_obj.components_

    target_columns = 3 if len(trait_list) > 2 else 2
    traits_loadings = list(loadings.T)

    return [list(trait_loading[:target_columns]) for trait_loading in traits_loadings]


def fetch_sample_datas(target_samples: List,
                       target_sample_data: dict,
                       this_samples_data: dict) ->Tuple[List[float], List[float]]:
    """get shared sample data xtodo refactor to use correlation"""

    target_trait_vals = []
    this_trait_vals = []

    for sample in target_samples:
        if sample in set(target_sample_data).intersection(this_samples_data):
            target_trait_vals.append(target_sample_data[sample].value)
            this_trait_vals.append(this_samples_data[sample].value)

        else:
            # remove sample key from shared
            pass

    return (this_trait_vals, target_trait_vals)


def compute_corr_matrix(trait_lists: List) -> Tuple[List, List]:
    """code for generating the correlation matrix"""
    corr_results = []
    pearson_results = []

    for (this_trait, this_dataset) in trait_lists:
        _this_db_samples = this_dataset.group.all_samples_ordered()

        this_trait_data = this_trait.data

        corr_row_input = []
        for (target_trait, target_dataset) in trait_lists:

            target_db_samples = target_dataset.group.all_samples_ordered()
            results = fetch_sample_datas(target_samples=target_db_samples,
                                         target_sample_data=target_trait.data,
                                         this_samples_data=this_trait_data)

            corr_row_input.append((target_trait, results))

        corr_row_results, pca_row_results = compute_row_matrix(
            sample_datas=corr_row_input)
        corr_results.append(corr_row_results)
        pearson_results.append(pca_row_results)

    return (corr_results, pearson_results)


def compute_row_matrix(sample_datas):
    """function to compute correlation for trait to create row"""

    # xtodo add lowest overlap
    is_spearman = False
    pca_corr_row = []

    corr_row = []

    for (target_trait, pair_samples) in sample_datas:

        (trait_vals, target_vals) = (pair_samples)

        (filtered_trait_vals, filtered_target_vals,
         num_overlap) = normalize_values(trait_vals, target_vals)

        if num_overlap < 2:
            corr_row.append([target_trait, 0, num_overlap])
            pca_corr_row.append(0)

        pearson_r, pearson_p = compute_corr_coeff_p_value(
            filtered_trait_vals, filtered_target_vals, "pearson")

        if is_spearman:
            (sample_r, _sample_p) = compute_corr_coeff_p_value(
                filtered_trait_vals, filtered_target_vals, "spearman")
        else:
            (sample_r, _sample_p) = (pearson_r, pearson_p)
            if sample_r > 0.999:
                is_spearman = True

        corr_row.append([target_trait, sample_r, num_overlap])
        pca_corr_row.append(pearson_r)

    return [corr_row, pca_corr_row]


def generate_pca_traits(pca_traits,
                        temp_dataset,
                        this_group_name,
                        shared_samples_list):
    """function to generate pca traits and temp vals"""

    pca_trait_dict = {}
    temp_dataset.group.get_samplelist()
    for i, pca_trait in enumerate(pca_traits):
        trait_id = "PCA" + str(i + 1) + "_" + temp_dataset.group.species + "_" + \
            this_group_name + "_" + datetime.datetime.now().strftime("%m%d%H%M%S")
        sample_vals = []
        pointer = 0
        for sample in temp_dataset.group.all_samples_ordered():
            if sample in shared_samples_list:
                sample_vals.append(str(pca_trait[pointer]))
                pointer += 1
            else:
                sample_vals.append("x")

        sample_vals = " ".join(sample_vals)

        pca_trait_dict[trait_id] = sample_vals
    return pca_trait_dict


def cache_pca_traits(redis_instance, pca_trait_dict, exp_time):
    """cache pca trait temp results """
    # xtodo

    for (trait, trait_vals) in pca_trait_dict.items():
        redis_instance.set(trait, trait_vals, ex=exp_time)
    return True
