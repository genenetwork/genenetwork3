"""module contains integration tests for correlation"""
from unittest import TestCase
from unittest import mock
from gn3.app import create_app


class CorrelationIntegrationTest(TestCase):
    """class for correlation integration tests"""

    def setUp(self):
        self.app = create_app().test_client()

    @mock.patch("gn3.api.correlation.compute_all_sample_correlation")
    def test_sample_r_correlation(self, mock_compute_samples):
        """Test /api/correlation/sample_r/{method}"""
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

    @mock.patch("gn3.api.correlation.compute_all_lit_correlation")
    @mock.patch("gn3.api.correlation.database_connector")
    def test_lit_correlation(self, database_connector, mock_compute_corr):
        """Test api/correlation/lit_corr/{species}/{gene_id}"""

        mock_compute_corr.return_value = []

        database_connector.return_value = (mock.Mock(), mock.Mock())

        post_data = {"1426678_at": "68031",
                     "1426679_at": "68036",
                     "1426680_at": "74777"}

        response = self.app.post(
            "/api/correlation/lit_corr/mouse/16", json=post_data, follow_redirects=True)

        self.assertEqual(mock_compute_corr.call_count, 1)
        self.assertEqual(response.status_code, 200)

    @mock.patch("gn3.api.correlation.compute_all_tissue_correlation")
    def test_tissue_correlation(self, mock_tissue_corr):
        """Test api/correlation/tissue_corr/{corr_method}"""
        mock_tissue_corr.return_value = {}

        target_trait_symbol_dict = {
            "1418702_a_at": "Bxdc1", "1412_at": "Bxdc2"}
        symbol_tissue_dict = {
            "bxdc1": [12, 21.1, 11.4, 16.7], "bxdc2": [12, 20.1, 12.4, 1.1]}

        primary_dict = {"trait_id": "1449593_at", "tissue_values": [1, 2, 3]}

        target_tissue_data = {
            "trait_symbol_dict": target_trait_symbol_dict,
            "symbol_tissue_vals_dict": symbol_tissue_dict
        }

        tissue_corr_input_data = {"primary_tissue": primary_dict,
                                  "target_tissues_dict": target_tissue_data}

        response = self.app.post("/api/correlation/tissue_corr/spearman",
                                 json=tissue_corr_input_data, follow_redirects=True)

        self.assertEqual(response.status_code, 200)
