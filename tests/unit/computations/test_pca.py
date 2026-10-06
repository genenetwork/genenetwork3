"""module contains unittests for pca"""
import unittest
from unittest.mock import patch
from unittest.mock import Mock

import numpy as np
import pytest
from scipy import stats
from sklearn import preprocessing
from sklearn.decomposition import PCA

from gn3.computations.pca import cache_pca_dataset
from gn3.computations.pca import compute_pca
from gn3.computations.pca import correlation_matrix_eigendecomposition
from gn3.computations.pca import generate_pca_temp_traits
from gn3.computations.pca import generate_pca_traits_vals
from gn3.computations.pca import generate_scree_plot_data
from gn3.computations.pca import process_factor_loadings_tdata


class TestPCA(unittest.TestCase):
    """pca testcase class"""

    @pytest.mark.unit_test
    def test_process_factor_loadings(self):
        """test for processing factor loadings"""

        test_array = np.array([
            [-0.23511749, -0.61483617, -0.26872797,  0.70319381],
            [-0.71057342,  0.4623377, -0.52921008, -0.0355803],
            [-0.60977093, -0.02877103, 0.78874096,  0.07238328],
            [0.26073856,  0.63827311,  0.16003023,  0.70640864]
        ])

        expected_results = [[-0.23511749, -0.71057342, -0.60977093],
                            [-0.61483617, 0.4623377, -0.02877103],
                            [-0.26872797, -0.52921008, 0.78874096],
                            [0.70319381, -0.0355803, 0.07238328]]

        self.assertEqual(process_factor_loadings_tdata(
            test_array, 3), expected_results)

    @pytest.mark.unit_test
    @patch("gn3.computations.pca.generate_pca_traits_vals")
    def test_generate_pca_datasets(self, mock_pca_data):
        """test for generating temp pca dataset"""

        mock_pca_data.return_value = np.array([[21, 10, 17, 15, 13],
                                               [21, 11, 18,
                                                9, 1],
                                               [22, 16, 0,
                                                0.22667229, -1],
                                               [31, 12, 10, 17, 11]])

        shared_samples = ["BXD1", "BXD2", "BXD", "BXD4", "Unkown"]

        dataset_samples = ["BXD1", "BXD5", "BXD4", "BXD"]
        expected_results = {
            "PCA1_mouse_G1_now": ["21.0",   "x",   "10.0",   "17.0"],
            "PCA2_mouse_G1_now": ["21.0",   "x",   "11.0",   "18.0"],
            "PCA3_mouse_G1_now": ["22.0",   "x",   "16.0",   "0.0"],
            "PCA4_mouse_G1_now": ["31.0",   "x",   "12.0",   "10.0"]
        }

        results = generate_pca_temp_traits(species="mouse", group="G1",
                                           traits_data=[],
                                           dataset_samples=dataset_samples,
                                           corr_array=[],
                                           shared_samples=shared_samples,
                                           create_time="now")

        self.assertEqual(results, expected_results)

    @pytest.mark.unit_test
    def test_generate_scree_plot(self):
        """test scree plot data is generated"""

        variance = [0.9271, 0.06232, 0.031]

        self.assertEqual(generate_scree_plot_data(variance),
                         (['PC1', 'PC2', 'PC3'], [92.7, 6.2, 3.1]))

    @pytest.mark.unit_test
    def test_cache_pca_datasets(self):
        """test for caching pca datasets"""

        pca_traits = {
            "PCA_1": ["11.0",   "x",   "9.0",   "7.0"],
            "PCA_2": ["x", "x", "1.2", "3.1"]
        }

        self.assertEqual(cache_pca_dataset(redis_conn={}, exp_days=30,
                                           pca_trait_dict=pca_traits), False)

        mock_redis = Mock()
        mock_redis.set.return_value = True

        test_data = [({}, 30, pca_traits, False),
                     (mock_redis, 30, pca_traits, True)]

        for (test_redis, exp_day, test_traits, expected) in test_data:

            with self.subTest(redis_conn=test_redis,
                              exp_days=exp_day, pca_trait_dict=test_traits):

                self.assertEqual(cache_pca_dataset(
                    test_redis, exp_day, test_traits), expected)


def sample_strain_means():
    """
    10 samples x 4 traits, deterministic and with distinct correlations so the
    eigen decomposition is unambiguous.
    """

    return np.array([
        [2.1, 8.2, 5.0, 1.0],
        [3.4, 6.5, 7.5, 4.0],
        [1.2, 7.1, 7.7, 1.5],
        [5.6, 3.3, 5.4, 3.0],
        [4.3, 4.9, 2.7, 4.5],
        [6.1, 2.6, 2.1, 1.2],
        [7.2, 3.8, 4.2, 3.9],
        [5.4, 5.1, 7.0, 4.2],
        [8.1, 1.9, 7.9, 1.1],
        [9.3, 2.2, 6.2, 3.4],
    ])


class TestCorrelationMatrixPCA(unittest.TestCase):
    """
    The principal components of a set of traits are the eigen vectors of their
    correlation matrix. Both the loadings table and the mapped PCA traits must
    come from that decomposition.

    Regression tests for two bugs:
      1. `compute_pca` ran PCA on the *column-standardised correlation matrix*,
         which is the eigen decomposition of corr(corr) rather than of corr.
      2. `generate_pca_traits_vals` standardised along the wrong axis and
         dropped the transpose of the eigen vectors.
    """

    @pytest.mark.unit_test
    def test_correlation_matrix_eigendecomposition(self):
        """the eigen values/vectors are ordered and orthonormal"""

        strain_means = sample_strain_means()
        traits_num = strain_means.shape[1]
        corr = np.corrcoef(strain_means, rowvar=False)

        (eigen_values, eigen_vectors) = correlation_matrix_eigendecomposition(
            corr)

        self.assertEqual(len(eigen_values), traits_num)
        self.assertTrue(np.all(np.diff(eigen_values) <= 0))
        self.assertTrue(np.allclose(
            eigen_vectors.T @ eigen_vectors, np.eye(traits_num)))

    @pytest.mark.unit_test
    def test_eigen_vectors_have_a_deterministic_sign(self):
        """
        The sign of an eigen vector is arbitrary, so it is anchored on the
        largest loading. For a positively correlated set of traits PC1 must
        therefore load positively on every trait (Perron-Frobenius), instead
        of coming back all-negative as numpy's `eigh` likes to return it.
        """

        rng = np.random.default_rng(3)
        common = rng.normal(size=56)
        strain_means = np.column_stack(
            [common + rng.normal(size=56) * 0.7 for _ in range(6)])
        corr = np.corrcoef(strain_means, rowvar=False)

        (_eigen_values, eigen_vectors) = correlation_matrix_eigendecomposition(
            corr)
        components = compute_pca(corr)["components"]

        self.assertTrue(np.all(eigen_vectors[:, 0] > 0))
        self.assertTrue(np.all(components[0] > 0))

    @pytest.mark.unit_test
    def test_compute_pca_is_the_eigen_decomposition_of_corr(self):
        """one component per trait, and each really is an eigen vector"""

        strain_means = sample_strain_means()
        traits_num = strain_means.shape[1]
        corr = np.corrcoef(strain_means, rowvar=False)

        pca_dict = compute_pca(corr)

        components = pca_dict["components"]
        variance_ratio = pca_dict["explained_variance_ratio"]

        self.assertEqual(components.shape, (traits_num, traits_num))
        self.assertEqual(len(variance_ratio), traits_num)
        self.assertAlmostEqual(float(variance_ratio.sum()), 1.0)
        self.assertTrue(np.all(np.diff(variance_ratio) <= 0))

        # trace(corr) == traits_num, so eigen_value_i == ratio_i * traits_num
        eigen_values = variance_ratio * traits_num
        self.assertTrue(np.allclose(
            corr @ components.T, components.T * eigen_values))

    @pytest.mark.unit_test
    def test_compute_pca_does_not_standardise_the_correlation_matrix(self):
        """guards against re-introducing the corr(corr) decomposition"""

        strain_means = sample_strain_means()
        corr = np.corrcoef(strain_means, rowvar=False)

        variance_ratio = compute_pca(corr)["explained_variance_ratio"]

        # what the old implementation produced: PCA of `preprocessing.scale(corr)`
        second_order = PCA().fit(preprocessing.scale(np.array(corr)))

        self.assertFalse(np.allclose(
            variance_ratio, second_order.explained_variance_ratio_))

    @pytest.mark.unit_test
    def test_generate_pca_traits_vals_matches_standard_pca(self):
        """the mapped traits are the scores of a standard PCA"""

        strain_means = sample_strain_means()
        samples_num, traits_num = strain_means.shape
        corr = np.corrcoef(strain_means, rowvar=False)

        # the traits are passed in as traits x samples
        pca_traits = generate_pca_traits_vals(strain_means.T, corr)

        zscores = (strain_means - strain_means.mean(axis=0)) / (
            strain_means.std(axis=0, ddof=1))
        reference = PCA().fit_transform(zscores)

        self.assertEqual(pca_traits.shape, (traits_num, samples_num))

        for idx in range(traits_num):
            # sign of an eigen vector is arbitrary, so compare magnitudes
            corr_coeff = np.corrcoef(pca_traits[idx], reference[:, idx])[0, 1]
            self.assertAlmostEqual(abs(corr_coeff), 1.0, places=8)

    @pytest.mark.unit_test
    def test_generate_pca_traits_vals_uses_the_displayed_loadings(self):
        """the displayed loadings are exactly the weights used to score traits"""

        strain_means = sample_strain_means()
        corr = np.corrcoef(strain_means, rowvar=False)
        trait_data_array = strain_means.T

        components = compute_pca(corr)["components"]
        trait_zscores = stats.zscore(trait_data_array, axis=1, ddof=1)

        expected = np.dot(components, trait_zscores)

        self.assertTrue(np.allclose(
            generate_pca_traits_vals(trait_data_array, corr), expected))
