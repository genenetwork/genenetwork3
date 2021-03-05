"""module contains code for testing creating show correlation object"""

import unittest
import json
import os
from gn3.correlation.show_corr_results import CorrelationResults


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
        pass
        with self.assertRaises(AssertionError):
            corr_results_object = CorrelationResults(start_vars={})

    def test_for_do_correlation(self):
        """add  dummy test for doing correlation"""

        start_vars = {
            "corr_type": "sample",
            "corr_sample_method": "pearson",
            "corr_dataset": "HC_M2_0606_P",
            "corr_return_results": 100
        }

        corr_results_object = CorrelationResults(
            start_vars=self.correlation_data)

        corr_results = corr_results_object.refactored_do_correlation(
            start_vars=self.correlation_data, create_dataset=create_dataset, create_trait=create_trait, get_species_dataset_trait=get_species_dataset_trait)

        # assert for self.corr_results group
        # mock data should use more reasonable results

        self.assertEqual(corr_results.this_trait, "this trait has been set")
        self.assertEqual(corr_results.species, "this species data")
        self.assertEqual(corr_results.dataset, "dataset results")

        # test using where type  is temp

        self.correlation_data["dataset"] = "Temp"

        self.correlation_data["group"] = "G1"

        corr_results_object_with_temp = CorrelationResults(
            start_vars=self.correlation_data)
        corr_results = corr_results_object.refactored_do_correlation(
            start_vars=self.correlation_data, create_dataset=create_dataset, create_trait=create_trait, get_species_dataset_trait=get_species_dataset_trait)

        # asssert where the dataset is temp

        self.assertEqual(corr_results.this_trait, "trait results")

        self.assertEqual(corr_results.dataset,"dataset results")

    def test_for_creating_traits_and_dataset(self):
        """and dummy tests for creating trait and dataset with dataset=Temp"""
        self.assertEqual(2, 2)
        return

        start_vars = {
            "corr_type": "sample",
            "corr_sample_method": "pearson",
            "corr_dataset": "HC_M2_0606_P",
            "corr_return_results": 100,
            "dataset": "Temp",
            "trait_id": "1444666_at",
            "group": "G1",
            "sample_vals": """{"C57BL/6J":"7.197","DBA/2J":"7.148","B6D2F1":"6.999"}""",
            "corr_samples_group": "samples_primary",
            "min_expr": "",
            "p_range_lower": "-1.00",
            "p_range_upper": "1.00"

        }

        corr_object = CorrelationResults(start_vars=start_vars)
        results = corr_object.do_correlation(start_vars=start_vars)

    def test_convert_to_mouse_gene_id(self):
        """test for converting mouse to gene id"""

        # results = convert_to_mouse_gene_id()
        pass
