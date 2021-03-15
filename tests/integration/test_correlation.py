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

    @mock.patch("gn3.api.correlation.compute_all_sample_correlation")
    def test_sample_r_correlation(self, mock_compute_samples):
        """test for  /api/correlation/sample_r"""
        this_trait_data = {
            "trait_id": "1455376_at",
            "trait_sample_data": {
                "C57BL/6J": "6.138",
                "DBA/2J": "6.266",
                "B6D2F1": "6.434",
                "D2B6F1": "6.55",
                "BXS2": "6.7"
            }}

        traits_dataset = [
            {
                "trait_id": "14192_at",
                "trait_sample_data": {
                    "DBA/2J": "7.13",
                    "D2B6F1": "5.65",
                    "BXD2": "1.46"
                }
            }
        ]

        correlation_input_data = {"corr_method": "pearson",
                                  "this_trait": this_trait_data,
                                  "target_dataset": traits_dataset}

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

        mock_compute_samples.return_value = expected_results

        api_response = {
            "corr_results": expected_results
        }

        response = self.app.post("/api/correlation/sample_r/pearson",
                                 json=correlation_input_data, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), api_response)
