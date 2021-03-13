"""module for testing correlation/correlation_computations"""

import unittest
from gn3.correlation.correlation_computations import compute_correlation


# mock for calculating correlation function

def mock_get_loading_page_data(initial_start_vars):
    """function to mock  filtering input"""
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

        return {
            "results": "success"
        }


class TestCorrelationUtility(unittest.TestCase):
    """tests for correlation computations"""

    def test_compute_correlation(self):
        """test function for doing correlation"""

        sample_vals = """{"C57BL/6J":"7.197","DBA/2J":"7.148","B6D2F1":"6.999"}"""

        correlation_input_data = {
            "wanted_inputs": "sample_vals,dataset,genofile,primary_samples",
            "genofile": "SAMPLE:X",
            "dataset": "HC_M2_0606_P",

            "sample_vals": sample_vals,
            "primary_samples": "C57BL/6J,DBA/2J,B6D2F1"

        }
        correlation_results = compute_correlation(
            correlation_input_data=correlation_input_data,
            correlation_results=MockCorrelationResults)
        results = {"results": "success"}

        self.assertEqual(results,correlation_results)
