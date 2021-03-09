"""module contains code for testing creating show correlation object"""

import unittest
import json
import os
from gn3.correlation.show_corr_results import CorrelationResults
from gn3.correlation.correlation_utility import AttributeSetter
from unittest import mock
class MockGroup:
    def __init__(self):
        self.samplelist = "add a mock for this"
        self.parlist = None

        self.filist = None


class MockCreateTrait:
    def __init__(self):
        pass

    def get_dict(self):
        raise NotImplementedError()

    def __str__(self):
        return self.__class__.__name__


class MockCreateDataset:
    def __init__(self):

        self.group = MockGroup()

    def get_trait_data(self, sample_keys):
        raise NotImplementedError()

    def retrieve_genes(symbol):
        raise NotImplementedError()


def file_path(relative_path):
    # adopted from github
    dir = os.path.dirname(os.path.abspath(__file__))
    split_path = relative_path.split("/")
    new_path = os.path.join(dir, *split_path)
    return new_path


def create_trait(dataset="Temp", name=None, cellid=None):
    return "trait results"


def create_dataset(dataset_name="Temp", dataset_type="Temp", group_name=None):
    return "dataset results"


def get_species_dataset_trait(self, start_vars):
    """
    how this function works is that it sets the self.dataset and self.species and self.this_trait
    """
    from types import SimpleNamespace


    with open(file_path("./dataset.json")) as dataset_file:
        results = json.load(dataset_file)
        self.dataset = SimpleNamespace(**results)

    with open(file_path("./group_data_test.json")) as group_file:
        results = json.load(group_file)
        self.group = SimpleNamespace(**results)
    

    self.dataset.group =  self.group

    trait_dict = {'name': '1434568_at', 'dataset': self.dataset,'cellid': None, 'identification': 'un-named trait', 'haveinfo': True, 'sequence': None}

    trait_obj = SimpleNamespace(**trait_dict)

    self.this_trait = trait_obj

    self.species = "this species data"


class TestCorrelationResults(unittest.TestCase):

    def setUp(self):

        with open(file_path("./correlation_test_data.json")) as json_file:
            self.correlation_data = json.load(json_file)

    def tearDown(self):

        self.correlation_data = ""

    def test_for_assertion(self):
        """test for assertion failures"""
        with self.assertRaises(AssertionError):
            corr_results_object = CorrelationResults(start_vars={})

    
    @mock.patch("gn3.correlation.show_corr_results.CorrelationResults.process_samples")
    def test_do_correlation(self,process_samples):
        """test for doing correlation"""
        process_samples.return_value = None
        corr_object = CorrelationResults(start_vars=self.correlation_data)


        with self.assertRaises(Exception) as error:

            #todo  to be completed



            corr_results = corr_object.do_correlation(start_vars=self.correlation_data,create_dataset=create_dataset,
                create_trait=None,get_species_dataset_trait=get_species_dataset_trait)
