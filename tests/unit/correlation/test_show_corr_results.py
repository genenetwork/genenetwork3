"""module contains code for testing creating show correlation object"""

import unittest
from gn3.correlation.show_corr_results import CorrelationResults


class TestCorrelationResults(unittest.TestCase):
    def test_for_assertion(self):
        with self.assertRaises(AssertionError):
            corr_results_object = CorrelationResults(start_vars={})

    def test_for_do_correlation(self):
        """add  dummy test for doing correlation"""

        start_vars = {
            "corr_type": "sample",
            "corr_sample_method": "pearson",
            "corr_dataset": "HC_M2_0606_P",
            "corr_return_results": 100
        }

        corr_results_object = CorrelationResults(start_vars=start_vars)

        # results = corr_results_object.do_correlation()
        # self.assertEqual(results,{
  #      "success":"data"
  #     })

    def test_for_creating_traits_and_dataset(self):
        """and dummy tests for creating trait and dataset with dataset=Temp"""

        start_vars = {
            "corr_type": "sample",
            "corr_sample_method": "pearson",
            "corr_dataset": "HC_M2_0606_P",
            "corr_return_results": 100,
            "dataset": "Temp",
            "trait_id": "1444666_at",
            "group": "G1",
            "sample_vals": """{"C57BL/6J":"7.197","DBA/2J":"7.148","B6D2F1":"6.999"}""",
            "corr_samples_group": "samples_primary",
            "min_expr": "",
            "p_range_lower": "-1.00",
            "p_range_upper": "1.00"

        }

        corr_object = CorrelationResults(start_vars=start_vars)
        results = corr_object.do_correlation(start_vars=start_vars)

        # no assertionError
