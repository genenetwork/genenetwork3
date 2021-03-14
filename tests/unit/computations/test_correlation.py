"""module contains the tests for correlation"""
from unittest import TestCase
from unittest import mock

from gn3.computations.correlations import normalize_values
from gn3.computations.correlations import do_bicor
from gn3.computations.correlations import compute_sample_r_correlation
from gn3.computations.correlations import compute_all_sample_correlation
from gn3.computations.correlations import filter_shared_sample_keys
from gn3.computations.correlations import tissue_lit_corr_for_probe_type


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

    def test_filter_shared_sample_keys(self):
        """function to  tests shared key between two dicts"""

        this_samplelist = {
            "C57BL/6J": "6.638",
            "DBA/2J": "6.266",
            "B6D2F1": "6.494",
            "D2B6F1": "6.565",
            "BXD2": "6.456"
        }

        target_samplelist = {
            "DBA/2J": "1.23",
            "D2B6F1": "6.565",
            "BXD2": "6.456"

        }

        filtered_target_samplelist = ["1.23", "6.565", "6.456"]
        filtered_this_samplelist = ["6.266", "6.565", "6.456"]

        results = filter_shared_sample_keys(
            this_samplelist=this_samplelist, target_samplelist=target_samplelist)

        self.assertEqual(results, (filtered_this_samplelist,
                                   filtered_target_samplelist))

    @mock.patch("gn3.computations.correlations.compute_sample_r_correlation")
    @mock.patch("gn3.computations.correlations.filter_shared_sample_keys")
    def test_compute_all_sample(self, filter_shared_samples, sample_r_corr):
        """given target dataset compute all sample r correlation"""

        filter_shared_samples.return_value = (["1.23", "6.565", "6.456"], [
            "6.266", "6.565", "6.456"])
        sample_r_corr.return_value = ([-1.0, 0.9, 6])

        this_trait_data = {
            "C57BL/6J": "6.638",
            "DBA/2J": "6.266",
            "B6D2F1": "6.494",
            "D2B6F1": "6.565",
            "BXD2": "6.456"
        }

        traits_dataset = [{
            "DBA/2J": "1.23",
            "D2B6F1": "6.565",
            "BXD2": "6.456"
        }]

        sample_all_results = [{"corr_coeffient": -1.0,
                               "p_value": 0.9,
                               "num_overlap": 6}]
        # ?corr_method: str, trait_vals, target_samples_vals

        self.assertEqual(compute_all_sample_correlation(
            this_trait=this_trait_data, target_dataset=traits_dataset), sample_all_results)
        sample_r_corr.assert_called_once_with(
            corr_method="pearson", trait_vals=['1.23', '6.565', '6.456'],
            target_samples_vals=['6.266', '6.565', '6.456'])
        filter_shared_samples.assert_called_once_with(
            this_trait_data, traits_dataset[0])

    def test_tissue_lit_corr_for_probe_type(self):
        """tests for doing tissue and lit correlation for  trait list\
        if both the dataset and target dataset are probeset"""

        results = tissue_lit_corr_for_probe_type(this_dataset_type=None,
                                                 target_dataset_type=None)

        self.assertEqual(results, (None, None))
