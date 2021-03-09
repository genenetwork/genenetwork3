"""module contains code for testing creating show correlation object"""

import unittest
import json
import os
from unittest import mock
from types import SimpleNamespace
from gn3.correlation.show_corr_results import CorrelationResults
# pylint: disable=unused-argument


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
