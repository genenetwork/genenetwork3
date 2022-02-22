"""module contains unittests for pca"""
import unittest

from gn3.computations.principal_component_analysis import compute_pca
from gn3.computations.principal_component_analysis import process_factor_loadings_tdata
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

                assert_allclose(
                    compute_zscores(test_array, axis, ddof), expected)

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
