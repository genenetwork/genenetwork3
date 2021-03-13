"""module contains integration tests for correlation"""
from unittest import TestCase
from unittest import mock
from gn3.app import create_app


class CorrelationIntegrationTest(TestCase):
    """class for correlation integration tests"""

    def setUp(self):
        self.app = create_app().test_client()

    def test_fail(self):
        """initial method for class that fails"""
        self.assertEqual(2, 2)

    @mock.patch("gn3.api.correlation.compute_sample_r_correlation")
    def test_sample_r_correlation(self, mock_compute_sample):
        """test for  /api/correlation/sample_r"""
        correlation_input_data = {"corr_method": "pearson",
                                  "trait_vals": [1, 2, 3],
                                  "target_samples_vals": [6.7, 1.4, 1.1]}
        expected_results = [
            {
                "sample_r": "-0.407",
                "p_value": "6.234e-04"
            },
            {
                "sample_r": "0.398",
                "sample_p": "8.614e-04"
            }
        ]

        mock_compute_sample.return_value = expected_results

        api_response = {
            "results": expected_results
        }

        response = self.app.post("/api/correlation/sample_r",
                                 json=correlation_input_data, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), api_response)
