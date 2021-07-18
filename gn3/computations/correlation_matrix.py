"""module contains code for computing pca using sklearn"""

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

    data = {

        "title": "Scree Plot",
        "ylabel": "Percentage  of Total variance %",
        "x_vals": x_vals,
        "y_vals": perc_var

    }

    return data


def fetch_sample_datas(target_samples: List,
                       target_sample_data: dict,
                       this_samples_data: dict) ->Tuple[List[float], List[float]]:
    """get shared sample data xtodo refactor to use correlation"""

    # xtodo refactor correlation signature in /computation/correlation

    # intenal of tsamples = ["BXD1","BXD2","BXD3"]
    # internal representaito of sample data is {"bxd":obj(val),bxd:obj(val)}

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

    for trait_db in trait_lists:
        this_trait = trait_db[0]
        _this_dataset = trait_db[1]

        # fetch required samples (fetch sample data) inputs for each

        this_trait_data = this_trait.data

        corr_row_input = []
        # n*n ????c

        for target_db in trait_lists:
            target_trait = target_db[0]
            _target_dataset = target_db[1]

            # get required sample datas
            # split this function too doing to much

            target_trait_data = target_trait.data

            corr_input = (target_trait, (this_trait_data, target_trait_data))

            corr_row_input.append(corr_input)

        pca_row_results, corr_row_results = compute_row_matrix(
            sample_datas=corr_row_input)
        corr_results.append(corr_row_results)
        pearson_results.append(pca_row_results)

    return (corr_results, pearson_results)


def compute_row_matrix(sample_datas):
    """function to compute correlation for trait to create row"""

    # expected inputs [[targ1,target2],[targ3,target4]]

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

        # normalize the values

    return [corr_row, pca_corr_row]


def fetch_corr_inputs(trait_lists: List):
    """function to get required corr inputs and parse them"""

    _results = trait_lists

    return []
