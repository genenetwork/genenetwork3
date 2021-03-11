"""module contains code for testing creating show correlation object"""

import unittest
import json
import os
from unittest import mock
from types import SimpleNamespace
from gn3.correlation.show_corr_results import CorrelationResults
from gn3.correlation.show_corr_results import get_header_fields
from gn3.correlation.show_corr_results import generate_corr_json
# pylint: disable=unused-argument



class AttributeSetter:
    """should refactot to use named tuple"""
    def __init__(self, trait_obj):
        for key, value in trait_obj.items():
            setattr(self, key, value)

class MockGroup:
    """mock  class for Group"""

    def __init__(self):
        self.samplelist = "add a mock for this"
        self.parlist = None

        self.filist = None

    def __str__(self):
        return self.__class__.__name__

    def get_dict(self):
        """get obj dict"""
        return self.__dict__


class MockCreateTrait:
    """mock class for create trait"""

    def __init__(self):
        pass

    def get_dict(self):
        """class for getting dict items"""
        return self.__dict__

    def __str__(self):
        return self.__class__.__name__


class MockCreateDataset:
    """mock class for create dataset"""

    def __init__(self):

        self.group = MockGroup()

    def get_trait_data(self, sample_keys):
        """method for getting trait data"""
        raise NotImplementedError()

    def retrieve_genes(self, symbol):
        """method for retrieving genes"""
        raise NotImplementedError()


def file_path(relative_path):
    """getting abs path for file """
    # adopted from github
    dir_name = os.path.dirname(os.path.abspath(__file__))
    split_path = relative_path.split("/")
    new_path = os.path.join(dir_name, *split_path)
    return new_path


def create_trait(dataset="Temp", name=None, cellid=None):
    """mock function for creating trait"""
    return "trait results"


def create_dataset(dataset_name="Temp", dataset_type="Temp", group_name=None):
    """mock  function to create dataset """
    return "dataset results"


def get_species(self, start_vars):
    """
    how this function works is that it sets the self.dataset and self.species and self.this_trait
    """

    with open(file_path("./dataset.json")) as dataset_file:
        results = json.load(dataset_file)
        self.dataset = SimpleNamespace(**results)

    with open(file_path("./group_data_test.json")) as group_file:
        results = json.load(group_file)
        self.group = SimpleNamespace(**results)

    self.dataset.group = self.group

    trait_dict = {'name': '1434568_at', 'dataset': self.dataset, 'cellid': None,
                  'identification': 'un-named trait', 'haveinfo': True, 'sequence': None}

    trait_obj = SimpleNamespace(**trait_dict)

    self.this_trait = trait_obj

    self.species = "this species data"


class TestCorrelationResults(unittest.TestCase):
    """unittests for Correlation Results"""

    def setUp(self):

        with open(file_path("./correlation_test_data.json")) as json_file:
            self.correlation_data = json.load(json_file)

    def tearDown(self):

        self.correlation_data = ""

    def test_for_assertion(self):
        """test for assertion failures"""
        with self.assertRaises(AssertionError):
            _corr_results_object = CorrelationResults(start_vars={})

    @mock.patch("gn3.correlation.show_corr_results.CorrelationResults.process_samples")
    def test_do_correlation(self, process_samples):
        """test for doing correlation"""
        process_samples.return_value = None
        corr_object = CorrelationResults(start_vars=self.correlation_data)

        with self.assertRaises(Exception) as _error:

            # xtodo;to be completed

            _corr_results = corr_object.do_correlation(start_vars=self.correlation_data,
                                                       create_dataset=create_dataset,
                                                       create_trait=None,
                                                       get_species_dataset_trait=get_species)



    def test_get_header_fields(self):
        expected = [
            ['Index',
             'Record',
             'Symbol',
             'Description',
             'Location',
             'Mean',
             'Sample rho',
             'N',
             'Sample p(rho)',
             'Lit rho',
             'Tissue rho',
             'Tissue p(rho)',
             'Max LRS',
             'Max LRS Location',
             'Additive Effect'],

            ['Index',
             'ID',
             'Location',
             'Sample r',
             'N',
             'Sample p(r)']

        ]
        result1 = get_header_fields("ProbeSet", "spearman")
        result2 = get_header_fields("Other", "Other")
        self.assertEqual(result1, expected[0])
        self.assertEqual(result2, expected[1])



    @mock.patch("gn3.utility.hmac.data_hmac")
    def test_generate_corr_json(self, mock_data_hmac):
        mock_data_hmac.return_value = "hajsdiau"

        dataset = AttributeSetter({"name": "the_name"})
        this_trait = AttributeSetter(
            {"name": "trait_test", "dataset": dataset})
        target_dataset = AttributeSetter({"type": "Publish"})
        corr_trait_1 = AttributeSetter({
            "name": "trait_1",
            "dataset": AttributeSetter({"name": "dataset_1"}),
            "view": True,
            "abbreviation": "T1",
            "description_display": "Trait I description",
            "authors": "JM J,JYEW",
            "pubmed_id": "34n4nn31hn43",
            "pubmed_text": "2016",
            "pubmed_link": "https://www.load",
            "lod_score": "",
            "mean": "",
            "LRS_location_repr": "BXBS",
            "additive": "",
            "sample_r": 10.5,
            "num_overlap": 2,
            "sample_p": 5




        })
        corr_results = [corr_trait_1]

        dataset_type_other = {
            "location": "cx-3-4",
            "sample_4": 12.32,
            "num_overlap": 3,
            "sample_p": 10.34
        }

        expected_results = '[{"index": 1, "trait_id": "trait_1", "dataset": "dataset_1", "hmac": "hajsdiau", "abbreviation_display": "T1", "description": "Trait I description", "mean": "N/A", "authors_display": "JM J,JYEW", "additive": "N/A", "pubmed_id": "34n4nn31hn43", "year": "2016", "lod_score": "N/A", "lrs_location": "BXBS", "sample_r": "10.500", "num_overlap": 2, "sample_p": "5.000e+00"}]'

        results1 = generate_corr_json(corr_results=corr_results, this_trait=this_trait,
                                      dataset=dataset, target_dataset=target_dataset, for_api=True)
        self.assertEqual(expected_results, results1)


    def test_generate_corr_json_view_false(self):
        trait = AttributeSetter({"view": False})
        corr_results = [trait]
        this_trait = AttributeSetter({"name": "trait_test"})
        dataset = AttributeSetter({"name": "the_name"})

        results_where_view_is_false = generate_corr_json(
            corr_results=corr_results, this_trait=this_trait, dataset={}, target_dataset={}, for_api=False)
        self.assertEqual(results_where_view_is_false, "[]")