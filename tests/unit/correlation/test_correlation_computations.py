"""module for testing correlation/correlation_computations"""

import unittest
from gn3.api.correlation import get_loading_page_data


class TestCorrelationUtility(unittest.TestCase):

    @staticmethod
    def create_start_initial_vars():
        return "item here"

    @staticmethod
    def mock_create_dataset():
        return {}

    @staticmethod
    def mock_get_genofile_samplelist():
        return {}

    def test_fails(self):
        """add test that fails"""
        print(get_loading_page_data)

        self.assertEqual(4, 4)

    def test_get_loading_page_data_no_data(self):
        """test loading page data function where initial start vars is None"""

        results = get_loading_page_data(
            initial_start_vars=None, create_dataset=None, get_genofile_samplelist=None)

        self.assertEqual(results, "no items")

    def test_get_loading_page_data(self):
        '''testing getting loading page data when n_samples key exists'''
        sample_vals = """{"C57BL/6J":7.197","DBA/2J":"7.148","B6D2F1":"6.999"}"""

        initial_start_vars = {
            "wanted_inputs": "sample_vals,corr_type,primary_samples,trait_id",

            "n_samples": "71",
            "wanted": "n_samples",

            "sample_vals": sample_vals,
            "primary_samples": "C57BL/6J,DBA/2J,B6D2F1"

        }

        results = get_loading_page_data(initial_start_vars=initial_start_vars, create_dataset=self.mock_create_dataset,
                                        get_genofile_samplelist=self.mock_get_genofile_samplelist)

        expected_starts_vars = {
            "n_samples": 71,
            "wanted_inputs": "sample_vals,corr_type,primary_samples,trait_id",

        }

        expected_starts_vars_container = {
        "start_vars":expected_starts_vars
        }

        self.assertEqual(expected_starts_vars, results["start_vars"])
        self.assertEqual(expected_starts_vars_container,results)
