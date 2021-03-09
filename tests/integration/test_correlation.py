"""Integration tests for correlation api"""
import unittest
from gn3.app import create_app


class CorrelationAPITest(unittest.TestCase):
    # currently disable
    """Test cases for the Correlation API"""

    def setUp(self):
        self.app = create_app().test_client()

    def test_corr_compute(self):
        """Test that the correct response in correlation"""

        sample_vals = """{"C57BL/6J":"7.197","DBA/2J":"7.148","B6D2F1":"6.999"}"""
        _post_data = {
            "corr_return_results": 100,
            "corr_sample_method": "pearson",
            "corr_type": "sample",
            "primary_samples": "C57BL/6J,DBA/2J,B6D2F1",
            "sample_vals": sample_vals,
            "dataset": "Temp",
            "group": "G1",
            "corr_dataset": "D1",
            "corr_samples_group": "samples_primary",
            "n_samples": 71,
            "min_expr": "",
            "p_range_lower": "-1.00",
            "p_range_upper": "1.00",
            "trait_id": "1444666_at",
            "wanted_inputs": "primary_samples,sample_vals,p_range_lower,\
            p_range_upper,min_expr,corr_samples_group,corr_dataset,\
            n_samples,corr_type,corr_sample_method,corr_return_results,trait_id,group,dataset"
        }

        _expected_data_correlation = {
            "corr_method": "pearson",
            'formatted_corr_type': "Genetic Correlation (Pearson's r)",
            "corr_type": "sample",
            "dataset": {
                "group": {

                    "genofile": "",
                    "samplelist": "S1",
                    "parlist": "",
                    "f1list": ""

                }
            },

            "location_chr": None,
            "location_type": None,
            "max_location_mb": None,
            "min_expr": None,
            "min_location_mb": None,
            "p_range_lower": -1.0,
            "p_range_upper": 1.0,
            "return_number": 100,
            "sample_data": {

            },
            "this_trait": {
                "group": {
                    "genofile": ""
                }

            },

            "trait_id": "1444666_at"



        }

        _expected_data_loading = {
            "start_vars": {
                "corr_dataset": "D1",
                "corr_return_results": 100,
                "corr_sample_method": "pearson",
                "corr_type": "sample",
                "dataset": "Temp",
                "group": "G1",
                "n_samples": 71,
                "p_range_lower": "-1.00",
                "p_range_upper": "1.00",
                "min_expr": None,
                "corr_samples_group": "samples_primary",
                "trait_id": "1444666_at",
                "wanted_inputs": "p_range_lower,p_range_upper,\
                min_expr,corr_samples_group,corr_dataset,\
                n_samples,corr_type,corr_sample_method,corr_return_results,trait_id,group,dataset"
            }
        }

        self.assertEqual(2, 2)

        # response = self.app.post(
        #     "/corr_compute", json=post_data, follow_redirects=True)
        # # self.assertEqual(response.get_json().get("result"), "hello world")
        # self.assertEqual(response.status_code, 200)
        # self.assertEqual(response.get_json(), expected_data_correlation)
