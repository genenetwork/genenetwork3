"""module contains integration tests for trait endpoints"""
from unittest import TestCase
from unittest import mock

from gn3.app import create_app


class TraitIntegrationTest(TestCase):
    """class contains integration tests for\
    traits"""

    def setUp(self):
        self.app = create_app().test_client()

    @mock.patch("gn3.api.traits.fetch_trait")
    @mock.patch("gn3.api.traits.database_connector")
    def test_create_trait(self, mock_database, mock_fetch_trait):
        """test the endpoint for creating traits\
        endpoint requires trait name and dataset name"""
        mock_database.return_value = (mock.Mock(), mock.Mock())
        trait_results = {
            "dataset": None,
            "trait_name": "1449593_at",
            "trait_data": {
                "BXD11": 8.464,
                "BXD12": 8.414,
                "BXD13": 8.753,
                "BXD15": 8.5,
                "BXD16": 8.832
            }

        }
        mock_fetch_trait.return_value = trait_results

        results = self.app.get(
            "/api/trait/1449593_at/HC_M2_0606_P", follow_redirects=True)

        trait_data = results.get_json()

        self.assertEqual(mock_database.call_count, 1)
        self.assertEqual(results.status_code, 200)
        self.assertEqual(trait_data, trait_results)

    @mock.patch("gn3.api.traits.get_trait_info_data")
    def test_retrieve_trait_info(self, mock_get_trait_info):
        """integration test for endpoints for retrieving\
        trait info expects the dataset of trait to have been
        created"""

        trait_post_data = {
            "trait": {"trait_name": ""},
            "trait_dataset": {"dataset_name": ""}
        }

        expected_api_results = {
            "description": "trait description",
            "chr": "",
            "locus": "",
            "mb": "",
            "abbreviation": "trait_abbreviation",
            "trait_display_name": "trait_name"

        }
        mock_get_trait_info.return_value = expected_api_results

        trait_info = self.app.post(
            "/api/trait/trait_info/144_at", json=trait_post_data, follow_redirects=True)

        trait_info_results = trait_info.get_json()

        self.assertEqual(trait_info.status_code, 200)
        self.assertEqual(trait_info_results, expected_api_results)
