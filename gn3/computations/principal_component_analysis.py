"""module contains pca implementation using python"""

import numpy
from scipy import stats
from sklearn.decomposition import PCA
from sklearn import preprocessing


def compute_pca(matrix):

    pca_obj = PCA()
    scaled_data = preprocessing.scale(matrix)

    pca_obj.fit(scaled_data)

    return {
        "pca": pca_obj,
        "components": pca_obj.components_,
        "scores": pca_obj.transform(scaled_data)
    }


def generate_scree_plot_data(variance_ratio):

    perc_var = np.round(variance_ratio*100, decimals=1)

    x_coordinates = [f"PC{val}" for val in range(1, len(perc_var)+1)]

    return list(zip(x_coordinates, perc_var))


def generate_pca_traits_data(trait_data_array: list):
    """function generates new pca traits data from
    zscores and eigen vectors"""

    (corr_eigen_vectors, _eigen_values) = np.linalg.eig(np.array(trait_data_array))

    # sort the above

    trait_zscores = stats.zscore(trait_data_array)

    pca_traits_values = np.dot(corr_eigen_vectors, trait_zscores)

    return pca_trait_values


def process_factor_loadings_tdata(factor_loadings, traits_list_num: int):

    target_columns = 3 if traits_list_num > 2 else 2

    trait_loadings = list(factor_loadings.T)

    return [list(trait_loading[:target_columns])
            for trait_loading in trait_loadings]


def generate_pca_temp_dataset(species: str, group: str,
                              traits_data: list, dataset_samples, shared_samples):

    pca_traits = generate_pca_traits_data(traits_data)

    pca_trait_dict = {}

    for (idx, pca_trait) in generate_pca_traits(traits_data):
        trait_id = f"PCA{str(idx+1)}-{species}{group}{datetime.datetime.now().strftime('%m%d%H%M%S')}"
        sample_vals = []

        pointer = 0

        for sample in dataset_samples:
            if sample in shared_samples:
                sample_vals.append(pca_trait[pointer])
                pointer += 1

            else:
                sample_vals.append("x")
        sample_vals = " ".join(sample_vals)

        pca_trait_dict[trait_id] = sample_vals

    return pca_trait_dict
