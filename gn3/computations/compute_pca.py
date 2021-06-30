"""module contains code for computing pca using sklearn"""

from typing import Dict
from typing import List

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.decomposition import PCA
from sklearn import preprocessing


def create_dataframe(traits_data: Dict[str, List[float]],
                     traits: List[str],
                     strain_names: List[str]):
    """create dt for col samples and rows as traits"""

    data = pd.DataFrame(columns=strain_names, index=traits)
    for trait in data.index:
        data.loc[trait, strain_names[0], strain_names[-1]
                 ] = traits_data[trait]

    return data


def compute_the_pca(data, transform: bool = True):
    """function to compute pca"""

    pca = PCA()

    if transform is True:
        # transform the matrix
        # e.g where samples are columns and traits are values
        scaled_data = preprocessing.scale(data.T)

    else:
        scaled_data = preprocessing.scale(data)

    # compute loading score and variaton of each pc

    # generate coordinates for pca graph if needd
    pca.fit(scaled_data)

    pca_data = pca.transform(scaled_data)

    return (pca, pca_data)


def get_trait_loading_scores(pca, traits=List[str]):
    """get the loadinng scores for first pca"""

    loading_scores = pd.Series(pca.components_[0], index=traits)

    # loading scores valu??---->

    return loading_scores


def plot_pca(pca, pca_data, strain_names: List[str]):
    """plot the pca not sure if needed"""

    perc_var = np.round(pca.explained_variance_ratio_*100, decimals=1)
    # get variance of labels

    labels = ["PC" + str(x) for x in range(1, len(perc_var)+1)]

    pca_df = pd.DataFrame(pca_data, index=strain_names, columns=labels)

    plt.scatter(pca_df.PC1, pca_df.PC2)
    for sample in pca_df.index:
        plt.annotate(sample, (pca_df.PC1.loc[sample], pca_df.PC2.loc[sample]))

    plt.title("")

    plt.xlabel("")
    plt.ylabel("")
    plt.show()
