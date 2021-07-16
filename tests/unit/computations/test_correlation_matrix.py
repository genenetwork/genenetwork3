"""module contains unittest for correlatiom matrix"""

import unittest
from types import SimpleNamespace
from gn3.computations.correlation_matrix import fetch_sample_datas
from gn3.computations.correlation_matrix import compute_row_matrix


class TestCorrelationMatrix(unittest.TestCase):
    """test for correlation matrix functions"""

    def test_fetch_sample_datas(self):
        """function to fetch both trait_vals and target_vals"""

        # target_sample and also this_sample

        # target_samples_keys ==target_samples ??????????????

        target_samples = ["C57BL/6J", "DBA/2J", "B6D2F1",
                          "D2B6F1", "BXD1", "BXD2", "BXD5", "BXD6"]

        target_samples_data = {"C57BL/6J": SimpleNamespace(value=1.2),
                               "B6D2F1": SimpleNamespace(value=2.1),
                               "BXD": SimpleNamespace(value=1.1),
                               "BXD12": SimpleNamespace(value=2.2),
                               "BXD5": SimpleNamespace(value=1.2),
                               "BXD6": SimpleNamespace(value=1.1)}

        this_samples_data = {"DBA/2J": SimpleNamespace(value=1.22),
                             "B6D2F1": SimpleNamespace(value=2.3),
                             "BXD1":    SimpleNamespace(value=1.1),
                             "BXD2": SimpleNamespace(value=2.2),
                             "BXD5": SimpleNamespace(value=1.2),
                             "BXD6": SimpleNamespace(value=1.1)}

        expected_target_trait_vals = [2.1, 1.2, 1.1]

        expected_this_trait_vals = [2.3, 1.2, 1.1]

        results = fetch_sample_datas(
            target_samples, target_samples_data, this_samples_data)

        self.assertEqual(results, (expected_this_trait_vals,
                                   expected_target_trait_vals))

    def test_compute_row_matrix(self):
        """Lower left cells list Pearson product-moment correlations;
        upper right cells list Spearman rank order correlations"""
        sample_datas = [[[1,2,3],[4,5,6]]]
        results = compute_row_matrix(sample_datas)

        self.assertFalse(results)
