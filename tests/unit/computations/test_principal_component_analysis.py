"""module contains unittests for pca"""
import unittest
from unittest.mock import patch
from unittest.mock import Mock

import numpy as np

from gn3.computations.principal_component_analysis import process_factor_loadings_tdata
from gn3.computations.principal_component_analysis import generate_pca_temp_dataset
from gn3.computations.principal_component_analysis import cache_pca_dataset
from gn3.computations.principal_component_analysis import generate_scree_plot_data


class TestPCA(unittest.TestCase):
    """pca testcase class"""

    def test_process_factor_loadings(self):
        """test for processing factor loadings"""

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

    @patch("gn3.computations.principal_component_analysis.generate_pca_traits_vals")
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
        expected_results = {"PCA1_mouse_G1_now": ["21.0",   'x',   "10.0",   "17.0"],
                            'PCA2_mouse_G1_now': ["21.0",   'x',   "11.0",   "18.0"],
                            'PCA3_mouse_G1_now': ["22.0",   'x',   "16.0",   "0.0"],
                            'PCA4_mouse_G1_now': ["31.0",   'x',   "12.0",   "10.0"]}

        self.assertEqual(generate_pca_temp_dataset(species="mouse", group="G1",
                                                   traits_data=[],
                                                   dataset_samples=dataset_samples,
                                                   corr_array=[],
                                                   shared_samples=shared_samples,
                                                   create_time="now"), expected_results)

    def test_generate_scree_plot(self):
        """test scree plot data is generated"""

        variance = [0.9271, 0.06232, 0.031]

        expected_results = [('PC1', 92.7), ('PC2', 6.2), ('PC3', 3.1)]

        self.assertEqual(generate_scree_plot_data(variance), expected_results)
