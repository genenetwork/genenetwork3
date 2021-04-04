"""this module contains integration tests for datasets"""
from unittest import TestCase
from unittest import mock

from collections import namedtuple
from gn3.app import create_app


class DatasetIntegrationTests(TestCase):
    """class contains integration tests for datasets"""

    def setUp(self):
        self.app = create_app().test_client()

    @mock.patch("gn3.api.datasets.create_dataset")
    def test_create_dataset(self, mock_dataset):
        """test for creating dataset object"""
        mock_dataset_creator = namedtuple(
            'ProbeSet', ["dataset_name", "dataset_type"])
        new_dataset = mock_dataset_creator("HC_M2_0606_P", "ProbeSet")
        mock_dataset.return_value = new_dataset
        response = self.app.get(
            "/api/dataset/create/HC_M2_0606_P/", follow_redirects=True)
        mock_dataset.assert_called_once_with(
            dataset_type=None, dataset_name="HC_M2_0606_P")
        results = response.get_json()["dataset"]
        self.assertEqual(results[1], "ProbeSet")
        self.assertEqual(response.status_code, 200)

    @mock.patch("gn3.api.datasets.get_traits_data")
    def test_fetch_traits_data(self, mock_get_trait_data):
        """test api/dataset/fetch_traits_data/d_name/d_type"""

        mock_get_trait_data.return_value = {}
        response = self.app.get(
            "/api/dataset/fetch_traits_data/Aging-Brain-UCIPublish/Publish")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json(), {"results": {}})
