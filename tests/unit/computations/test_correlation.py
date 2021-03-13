"""module contains the tests for correlation"""
from unittest import TestCase
from unittest import mock

from gn3.computations.correlations import normalize_values
from gn3.computations.correlations import do_bicor
from gn3.computations.correlations import compute_sample_r_correlation


class TestCorrelation(TestCase):
    """class for testing correlation functions"""

    def test_normalize_values(self):
        """function to test normalizing values """
        results = normalize_values([2.3, None, None, 3.2, 4.1, 5],
                                   [3.4, 7.2, 1.3, None, 6.2, 4.1])

        expected_results = ([2.3, 4.1, 5], [3.4, 6.2, 4.1], 3)

        self.assertEqual(results, expected_results)

    def test_bicor(self):
        """test for doing biweight mid correlation """

        results = do_bicor(x_val=[1, 2, 3], y_val=[4, 5, 6])

        self.assertEqual(results, ([1, 2, 3], [4, 5, 6])
                         )

    @mock.patch("gn3.computations.correlations.compute_corr_coeff_p_value")
    @mock.patch("gn3.computations.correlations.normalize_values")
    def test_compute_sample_r_correlation(self, norm_vals, compute_corr):
        """test for doing sample correlation gets the cor\
        and p value and rho value using pearson correlation"""
        primary_values = [2.3, 4.1, 5]
        target_values = [3.4, 6.2, 4.1]

        norm_vals.return_value = ([2.3, 4.1, 5, 4.2, 4, 1.2],
                                  [3.4, 6.2, 4, 1.1, 8, 1.1], 6)
        compute_corr.side_effect = [(0.7, 0.3), (-1.0, 0.9), (1, 0.21)]

        pearson_results = compute_sample_r_correlation(corr_method="pearson",
                                                       trait_vals=primary_values,
                                                       target_samples_vals=target_values)

        spearman_results = compute_sample_r_correlation(corr_method="spearman",
                                                        trait_vals=primary_values,
                                                        target_samples_vals=target_values)

        bicor_results = compute_sample_r_correlation(corr_method="bicor",
                                                     trait_vals=primary_values,
                                                     target_samples_vals=target_values)

        self.assertEqual(bicor_results, (1, 0.21, 6))
        self.assertEqual(pearson_results, (0.7, 0.3, 6))
        self.assertEqual(spearman_results, (-1.0, 0.9, 6))

        self.assertIsInstance(
            pearson_results, tuple, "message")
        self.assertIsInstance(
            spearman_results, tuple, "message")
