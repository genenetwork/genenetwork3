"""module for testing correlation/correlation_computations"""

import unittest
from gn3.api.correlation import get_loading_page_data


class AttributeSetter:
    def __init__(self, trait_obj):
        for key, value in trait_obj.items():
            setattr(self, key, value)


class TestCorrelationUtility(unittest.TestCase):

    @staticmethod
    def create_start_initial_vars():
        return "item here"

    @staticmethod
    def mock_create_dataset(dataset):

        dataset = AttributeSetter({
            "group": AttributeSetter({
                "genofile": ""
            })
        })

        return dataset

    @staticmethod
    def mock_get_genofile_samplelist(dataset):
        # should mock call to db
        return ["C57BL/6J"]

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
        sample_vals = """{"C57BL/6J":"7.197","DBA/2J":"7.148","B6D2F1":"6.999"}"""

        initial_start_vars = {

            "n_samples": "71",
            "wanted_inputs": "n_samples",

            "sample_vals": sample_vals,
            "primary_samples": "C57BL/6J,DBA/2J,B6D2F1"

        }

        results = get_loading_page_data(initial_start_vars=initial_start_vars, create_dataset=self.mock_create_dataset,
                                        get_genofile_samplelist=self.mock_get_genofile_samplelist)

        expected_starts_vars = {
            "n_samples": 71,
            "wanted_inputs": "n_samples",

        }

        expected_starts_vars_container = {
            "start_vars": expected_starts_vars
        }

        self.assertEqual(expected_starts_vars, results["start_vars"])
        self.assertEqual(expected_starts_vars_container, results)

    def test_get_loading_page_no_samples(self):
        '''testing getting loading page data when n_samples key don't exists'''

        sample_vals = """{"C57BL/6J":"7.197","DBA/2J":"7.148","B6D2F1":"6.999"}"""

        initial_start_vars = {
            "wanted_inputs": "sample_vals,dataset,genofile,primary_samples",
            "genofile": "SAMPLE:X",
            "dataset": "HC_M2_0606_P",

            "sample_vals": sample_vals,
            "primary_samples": "C57BL/6J,DBA/2J,B6D2F1"

        }

        results = get_loading_page_data(initial_start_vars=initial_start_vars, create_dataset=self.mock_create_dataset,
                                        get_genofile_samplelist=self.mock_get_genofile_samplelist)

        expected_results = {'start_vars': {'genofile': 'SAMPLE:X', 'dataset': 'HC_M2_0606_P', 'sample_vals': '{"C57BL/6J":"7.197","DBA/2J":"7.148","B6D2F1":"6.999"}',
                                           'primary_samples': 'C57BL/6J,DBA/2J,B6D2F1',
                                           'n_samples': 3, 'wanted_inputs':"sample_vals,dataset,genofile,primary_samples"}}

        self.assertEqual(results, expected_results)
