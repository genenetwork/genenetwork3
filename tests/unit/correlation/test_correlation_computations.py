"""module for testing correlation/correlation_computations"""

import unittest
from gn3.correlation.correlation_computations import filter_input_data
from gn3.correlation.correlation_computations import compute_correlation




# mock for calculating correlation function

def mock_get_loading_page_data(initial_start_vars):
    """function to mock  filtering input"""
    print(initial_start_vars)
    results = {'start_vars':
               {'genofile': 'SAMPLE:X', 'dataset': 'HC_M2_0606_P',
                'sample_vals': '{"C57BL/6J":"7.197","DBA/2J":"7.148","B6D2F1":"6.999"}',
                'primary_samples': 'C57BL/6J,DBA/2J,B6D2F1',
                'n_samples': 3,
                'wanted_inputs': "sample_vals,dataset,genofile,primary_samples"}}

    return results


class MockCorrelationResults:
    """mock class for CorrelationResults"""

    def __init__(self, start_vars):
        for _key, value in start_vars.items():
            self.value = value

        self.assert_start_vars(start_vars)

    @staticmethod
    def assert_start_vars(start_vars):
        """assert data required is supplied"""
        assert "wanted_inputs" in start_vars

    def do_correlation(self, start_vars):
        """mock method for doing correlation"""
        print(self.__class__.__name__)

        return {
            "success": start_vars
        }


class TestCorrelationUtility(unittest.TestCase):
    """tests for correlation computations"""

    def test_fails(self):
        """add test that fails"""

        self.assertEqual(4, 4)

    def test_filter_input_no_data(self):
        """test loading page data function where initial start vars is None"""
        with self.assertRaises(NotImplementedError):
            results = filter_input_data(initial_start_vars=None)
            self.assertEqual(results, None)

    def test_filter_input_data(self):
        '''testing getting loading page data when n_samples key exists'''
        sample_vals = """{"C57BL/6J":"7.197","DBA/2J":"7.148","B6D2F1":"6.999"}"""

        initial_start_vars = {

            "n_samples": "71",
            "wanted_inputs": "n_samples",

            "sample_vals": sample_vals,
            "primary_samples": "C57BL/6J,DBA/2J,B6D2F1"

        }

        results = filter_input_data(initial_start_vars=initial_start_vars)

        expected_starts_vars = {
            "n_samples": 71,
            "wanted_inputs": "n_samples",

        }

        expected_starts_vars_container = {
            "start_vars": expected_starts_vars
        }

        self.assertEqual(expected_starts_vars, results["start_vars"])
        self.assertEqual(expected_starts_vars_container, results)

    def test_compute_correlation(self):
        """test function for doing correlation"""

        sample_vals = """{"C57BL/6J":"7.197","DBA/2J":"7.148","B6D2F1":"6.999"}"""

        initial_start_vars = {
            "wanted_inputs": "sample_vals,dataset,genofile,primary_samples",
            "genofile": "SAMPLE:X",
            "dataset": "HC_M2_0606_P",

            "sample_vals": sample_vals,
            "primary_samples": "C57BL/6J,DBA/2J,B6D2F1"

        }
        correlation_object = compute_correlation(
            init_start_vars=initial_start_vars,
            get_input_data=mock_get_loading_page_data,
            correlation_results=MockCorrelationResults)

        results = {'genofile': 'SAMPLE:X', 'dataset': 'HC_M2_0606_P',
                   'sample_vals': '{"C57BL/6J":"7.197","DBA/2J":"7.148","B6D2F1":"6.999"}',
                   'primary_samples': 'C57BL/6J,DBA/2J,B6D2F1',
                   'n_samples': 3,
                   'wanted_inputs': "sample_vals,dataset,genofile,primary_samples"}

        self.assertEqual({
            "success": results
        }, correlation_object)
