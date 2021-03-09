"""module contains code for testing creating show correlation object"""

import unittest
import json
import os
from gn3.correlation.show_corr_results import CorrelationResults


class MockGroup:
    def __init__(self):
        self.samplelist = "add a mock for this"
        self.parlist = None

        self.filist = None


class MockCreateeDataset:
    def__init__(self):
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

    self.species = "this species data"
    self.dataset = "dataset results"
    self.this_trait = "this trait has been set"


class TestCorrelationResults(unittest.TestCase):

    def setUp(self):

        with open(file_path("./correlation_test_data.json")) as json_file:
            self.correlation_data = json.load(json_file)

    def tearDown(self):

        self.correlation_data = ""
        # pass

    def test_for_assertion(self):
        """test for assertion failures"""
        with self.assertRaises(AssertionError):
            corr_results_object = CorrelationResults(start_vars={})

    def test_do_correlation(self):

        # def test_for_do_correlation(self):
        #     """add  dummy test for doing correlation and creating trait and dataset"""

        #     corr_results_object = CorrelationResults(
        #         start_vars=self.correlation_data)

        #     corr_results = corr_results_object.do_correlation(
        #         start_vars=self.correlation_data, create_dataset=create_dataset, create_trait=create_trait, get_species_dataset_trait=get_species_dataset_trait)

        #     # assert for self.corr_results group
        #     # mock data should use more reasonable results

        #     self.assertEqual(corr_results.this_trait, "this trait has been set")
        #     self.assertEqual(corr_results.species, "this species data")
        #     self.assertEqual(corr_results.dataset, "dataset results")

        #     # test using where type  is temp

        #     self.correlation_data["dataset"] = "Temp"

        #     self.correlation_data["group"] = "G1"

        #     corr_results_object_with_temp = CorrelationResults(
        #         start_vars=self.correlation_data)
        #     corr_results = corr_results_object.refactored_do_correlation(
        #         start_vars=self.correlation_data, create_dataset=create_dataset, create_trait=create_trait, get_species_dataset_trait=get_species_dataset_trait)

        #     # asssert where the dataset is temp

        #     self.assertEqual(corr_results.this_trait, "trait results")

        #     self.assertEqual(corr_results.dataset, "dataset results")
        #     self.assertEqual(corr_results.trait_id, "1449593_at")
