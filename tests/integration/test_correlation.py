"""Integration tests for correlation api"""

import os
import json
import pickle
import unittest
from unittest import mock

from gn3.app import create_app


def file_path(relative_path):
    """getting abs path for file """
    dir_name = os.path.dirname(os.path.abspath(__file__))
    split_path = relative_path.split("/")
    new_path = os.path.join(dir_name, *split_path)
    return new_path


class CorrelationAPITest(unittest.TestCase):
    # currently disable
    """Test cases for the Correlation API"""

    def setUp(self):
        self.app = create_app().test_client()

        with open(file_path("correlation_data.json")) as json_file:
            self.correlation_data = json.load(json_file)

        with open(file_path("expected_corr_results.json")) as results_file:
            self.correlation_results = json.load(results_file)

    def tearDown(self):
        self.correlation_data = ""

        self.correlation_results = ""

    @mock.patch("gn3.api.correlation.compute_correlation")
    def test_corr_compute(self, compute_corr):
        """Test that the correct response in correlation"""

        compute_corr.return_value = self.correlation_results
        response = self.app.post(
            "/api/correlation/corr_compute", json=self.correlation_data, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
