"""Module contains tests for creating traits"""
from unittest import TestCase
from unittest import mock

from gn3.computations.traits import fetch_trait
from gn3.computations.traits import get_trait_sample_data
from gn3.computations.traits import get_trait_info_data


class TestTrait(TestCase):
    """Class contains tests for creating traits"""

    @mock.patch("gn3.computations.traits.get_trait_sample_data")
    def test_fetch_trait(self, get_sample_data):
        """Test for creating/fetching trait"""

        expected_sample_data = {
            "A/Y": 12.3,
            "WQC": 11.1
        }

        database = mock.Mock()

        get_sample_data.return_value = expected_sample_data

        expected_trait = {
            "trait_name": "AXFDSF_AT",
            "dataset": None,
            "trait_data": expected_sample_data
        }
        results = fetch_trait(dataset=None,
                              trait_name="AXFDSF_AT",
                              database=database)

        self.assertEqual(results, expected_trait)
        self.assertEqual(get_sample_data.call_count, 1)

    @mock.patch("gn3.computations.traits.retrieve_trait_sample_data")
    def test_get_trait_sample_data(self, mock_retrieve_sample_data):
        """Test for getting sample data from  either\
        the trait's dataset or form redis
        """

        trait_dataset = mock.Mock()
        dataset_trait_sample_data = [
            ('129S1/SvImJ', 7.433, None, None, '129S1/SvImJ'),
            ('A/J', 7.596, None, None, 'A/J'),
            ('AKR/J', 7.774, None, None, 'AKR/J'),
            ('B6D2F1', 7.707, None, None, 'B6D2F1')]
        mock_retrieve_sample_data.return_value = dataset_trait_sample_data

        trait_name = "1426679_at"

        database = mock.Mock()

        results = get_trait_sample_data(
            trait_dataset, trait_name, database)

        expected_results = {
            "129S1/SvImJ": 7.433,
            "A/J": 7.596,
            "AKR/J": 7.774,
            "B6D2F1": 7.707
        }

        self.assertEqual(results, expected_results)

    def test_get_trait_info_data(self):
        """Test for getting info data related\
        to trait
        """

        results = get_trait_info_data(
            trait_name="AXSF_AT", trait_dataset=mock.Mock(), database_instance=None)
        expected_trait_info = {
            "description": "",
            "trait_display_name": "",
            "abbreviation": "",
            "chr": "",
            "mb": "",
            "locus": ""
        }

        self.assertEqual(results, expected_trait_info)
