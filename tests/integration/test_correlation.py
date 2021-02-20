"""Integration tests for correlation api"""

import json
import unittest
from gn3.app import create_app


class CorrelationAPITest(unittest.TestCase):
    """Test cases for the Gemma API"""

    def setUp(self):
        self.app = create_app().test_client()

    def test_corr_compute(self):
        """Test that the correct response in correlation"""
        post_data = {
            "corr_return_results": 100,
            "corr_sample_method": "pearson",
            "corr_type": "sample",
            "dataset": "Temp",
            "group": "G1",
            "corr_dataset": "D1",
            "n_samples": 71,
            "trait_id": "1444666_at",
            "wanted_inputs": "corr_dataset,n_samples,corr_type,corr_sample_method,corr_return_results,trait_id,group,dataset"
        }

        expected_data = {
            "start_vars": {
                "corr_dataset": "D1",
                "corr_return_results": 100,
                "corr_sample_method": "pearson",
                "corr_type": "sample",
                "dataset": "Temp",
                "group": "G1",
                "n_samples": 71,
                "trait_id": "1444666_at",
                "wanted_inputs": "corr_dataset,n_samples,corr_type,corr_sample_method,corr_return_results,trait_id,group,dataset"
            }
        }

        response = self.app.post(
            "/corr_compute", json=post_data, follow_redirects=True)
        # self.assertEqual(response.get_json().get("result"), "hello world")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(),expected_data)
