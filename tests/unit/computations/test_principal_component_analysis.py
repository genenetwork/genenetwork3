"""module contains unittests for pca"""
import unittest
from unittest.mock import patch
from unittest.mock import Mock
from gn3.computations.principal_component_analysis import compute_pca
from gn3.computations.principal_component_analysis import process_factor_loadings_tdata
from gn3.computations.principal_component_analysis import generate_pca_temp_dataset
from gn3.computations.principal_component_analysis import cache_pca_dataset
from scipy.stats import random_correlation


import numpy as np
from numpy.testing import assert_allclose


class TestPCA(unittest.TestCase):
    """pca testcase class"""

    def test_compute_zscores(self):

        for test_array, axis, ddof, expected in [([0.7972,  0.0767,  0.4383,  0.7866,  0.8091,
                                                   0.1954,  0.6307,  0.6599,  0.1065,  0.0508], 0, 0,
                                                  [1.127246, -1.246996, -0.055426,  1.092316,  1.166459, -0.855847,
                                                   0.578583,  0.674805, -1.148797, -1.332343])]:
            with self.subTest(nums=test_array, axis=axis, ddof=ddof):
                pass

                # assert_allclose(
                #     compute_zscores(test_array, axis, ddof), expected)

    def test_compute_pca(self):

        rng = np.random.default_rng()

        x = random_correlation.rvs((.5, .8, 1.2, 1.5), random_state=rng)

        results = compute_pca(x)

        # self.assertEqual(results,[])

    def test_process_factor_loadings(self):

        test_array = np.array([[-0.23511749, -0.61483617, -0.26872797,  0.70319381],
                               [-0.71057342,  0.4623377, -0.52921008, -0.0355803],
                               [-0.60977093, -0.02877103,
                                   0.78874096,  0.07238328],
                               [0.26073856,  0.63827311,  0.16003023,  0.70640864]])

        expected_results = [[-0.23511749, -0.71057342, -0.60977093],
                            [-0.61483617, 0.4623377, -0.02877103],
                            [-0.26872797, -0.52921008, 0.78874096],
                            [0.70319381, -0.0355803, 0.07238328]]

        self.assertEqual(process_factor_loadings_tdata(
            test_array, 3), expected_results)

    @patch("gn3.computations.principal_component_analysis.generate_pca_traits_data")
    def test_generate_pca_datasets(self, mock_pca_data):
        # refactor test

        mock_pca_data.return_value = [[21, 10, 17, 15, 13],
                                      [21, 11, 18,
                                       9, 1],
                                      [22, 16, 0,
                                       0.22667229, -1],
                                      [31, 12, 10, 17, 11]]

        shared_samples = ["BXD1", "BXD2", "BXD", "BXD4", "Unkown"]

        dataset_samples = ["BXD1", "BXD5", "BXD4", "BXD"]
        #
    # datetime.datetime.now().strftime('%m%d%H%M%S')

        expected_results = {"PCA1-mouseG1now": [21,   'x',   10,   17],
                            'PCA2-mouseG1now': [21,   'x',   11,   18],
                            'PCA3-mouseG1now': [22,   'x',   16,   0],
                            'PCA4-mouseG1now': [31,   'x',   12,   10]}

        self.assertEqual(generate_pca_temp_dataset(species="mouse", group="G1",
                                                   traits_data=[], dataset_samples=dataset_samples, shared_samples=shared_samples, str_datetime="now"), expected_results)

    def test_cache_pca_datasets(self):

        mock_redis = Mock()
        mock_redis.set.return_value = None

        pca_trait_dict = {"PCA1-mouseG1now": [21,   'x',   10,   17],
                          'PCA2-mouseG1now': [21,   'x',   11,   18],
                          'PCA3-mouseG1now': [22,   'x',   16,   0],
                          'PCA4-mouseG1now': [31,   'x',   12,   10]}

        self.assertIs(cache_pca_dataset(mock_redis, 30, pca_trait_dict), True)
