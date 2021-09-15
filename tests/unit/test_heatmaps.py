"""Module contains tests for gn3.heatmaps.heatmaps"""
from unittest import TestCase
from gn3.heatmaps import (
    cluster_traits,
    get_lrs_from_chr,
    export_trait_data,
    compute_traits_order,
    retrieve_strains_and_values)

strainlist = ["B6cC3-1", "BXD1", "BXD12", "BXD16", "BXD19", "BXD2"]
trait_data = {
    "mysqlid": 36688172,
    "data": {
        "B6cC3-1": {"strain_name": "B6cC3-1", "value": 7.51879, "variance": None, "ndata": None},
        "BXD1": {"strain_name": "BXD1", "value": 7.77141, "variance": None, "ndata": None},
        "BXD12": {"strain_name": "BXD12", "value": 8.39265, "variance": None, "ndata": None},
        "BXD16": {"strain_name": "BXD16", "value": 8.17443, "variance": None, "ndata": None},
        "BXD19": {"strain_name": "BXD19", "value": 8.30401, "variance": None, "ndata": None},
        "BXD2": {"strain_name": "BXD2", "value": 7.80944, "variance": None, "ndata": None},
        "BXD21": {"strain_name": "BXD21", "value": 8.93809, "variance": None, "ndata": None},
        "BXD24": {"strain_name": "BXD24", "value": 7.99415, "variance": None, "ndata": None},
        "BXD27": {"strain_name": "BXD27", "value": 8.12177, "variance": None, "ndata": None},
        "BXD28": {"strain_name": "BXD28", "value": 7.67688, "variance": None, "ndata": None},
        "BXD32": {"strain_name": "BXD32", "value": 7.79062, "variance": None, "ndata": None},
        "BXD39": {"strain_name": "BXD39", "value": 8.27641, "variance": None, "ndata": None},
        "BXD40": {"strain_name": "BXD40", "value": 8.18012, "variance": None, "ndata": None},
        "BXD42": {"strain_name": "BXD42", "value": 7.82433, "variance": None, "ndata": None},
        "BXD6": {"strain_name": "BXD6", "value": 8.09718, "variance": None, "ndata": None},
        "BXH14": {"strain_name": "BXH14", "value": 7.97475, "variance": None, "ndata": None},
        "BXH19": {"strain_name": "BXH19", "value": 7.67223, "variance": None, "ndata": None},
        "BXH2": {"strain_name": "BXH2", "value": 7.93622, "variance": None, "ndata": None},
        "BXH22": {"strain_name": "BXH22", "value": 7.43692, "variance": None, "ndata": None},
        "BXH4": {"strain_name": "BXH4", "value": 7.96336, "variance": None, "ndata": None},
        "BXH6": {"strain_name": "BXH6", "value": 7.75132, "variance": None, "ndata": None},
        "BXH7": {"strain_name": "BXH7", "value": 8.12927, "variance": None, "ndata": None},
        "BXH8": {"strain_name": "BXH8", "value": 6.77338, "variance": None, "ndata": None},
        "BXH9": {"strain_name": "BXH9", "value": 8.03836, "variance": None, "ndata": None},
        "C3H/HeJ": {"strain_name": "C3H/HeJ", "value": 7.42795, "variance": None, "ndata": None},
        "C57BL/6J": {"strain_name": "C57BL/6J", "value": 7.50606, "variance": None, "ndata": None},
        "DBA/2J": {"strain_name": "DBA/2J", "value": 7.72588, "variance": None, "ndata": None}}}

slinked = (
    (((0, 2, 0.16381088984330505),
      ((1, 7, 0.06024619831474998), 5, 0.19179284676938602),
      0.20337048635536847),
     9,
     0.23451785425383564),
    ((3, (6, 8, 0.2140799896286565), 0.25879514152086425),
     4, 0.8968250491499363),
    0.9313185954797953)

class TestHeatmap(TestCase):
    """Class for testing heatmap computation functions"""

    def test_export_trait_data_dtype(self):
        """
        Test `export_trait_data` with different values for the `dtype` keyword
        argument
        """
        for dtype, expected in [
                ["val", (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["var", (None, None, None, None, None, None)],
                ["N", (None, None, None, None, None, None)],
                ["all", (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)]]:
            with self.subTest(dtype=dtype):
                self.assertEqual(
                    export_trait_data(trait_data, strainlist, dtype=dtype),
                    expected)

    def test_export_trait_data_dtype_all_flags(self):
        """
        Test `export_trait_data` with different values for the `dtype` keyword
        argument and the different flags set up
        """
        for dtype, vflag, nflag, expected in [
                ["val", False, False,
                 (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["val", False, True,
                 (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["val", True, False,
                 (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["val", True, True,
                 (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["var", False, False, (None, None, None, None, None, None)],
                ["var", False, True, (None, None, None, None, None, None)],
                ["var", True, False, (None, None, None, None, None, None)],
                ["var", True, True, (None, None, None, None, None, None)],
                ["N", False, False, (None, None, None, None, None, None)],
                ["N", False, True, (None, None, None, None, None, None)],
                ["N", True, False, (None, None, None, None, None, None)],
                ["N", True, True, (None, None, None, None, None, None)],
                ["all", False, False,
                 (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["all", False, True,
                 (7.51879, None, 7.77141, None, 8.39265, None, 8.17443, None,
                  8.30401, None, 7.80944, None)],
                ["all", True, False,
                 (7.51879, None, 7.77141, None, 8.39265, None, 8.17443, None,
                  8.30401, None, 7.80944, None)],
                ["all", True, True,
                 (7.51879, None, None, 7.77141, None, None, 8.39265, None, None,
                  8.17443, None, None, 8.30401, None, None, 7.80944, None, None)]
        ]:
            with self.subTest(dtype=dtype, vflag=vflag, nflag=nflag):
                self.assertEqual(
                    export_trait_data(
                        trait_data, strainlist, dtype=dtype, var_exists=vflag,
                        n_exists=nflag),
                    expected)

    def test_cluster_traits(self):
        """
        Test that the clustering is working as expected.
        """
        traits_data_list = [
            (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944),
            (6.1427, 6.50588, 7.73705, 6.68328, 7.49293, 7.27398),
            (8.4211, 8.30581, 9.24076, 8.51173, 9.18455, 8.36077),
            (10.0904, 10.6509, 9.36716, 9.91202, 8.57444, 10.5731),
            (10.188, 9.76652, 9.54813, 9.05074, 9.52319, 9.10505),
            (6.74676, 7.01029, 7.54169, 6.48574, 7.01427, 7.26815),
            (6.39359, 6.85321, 5.78337, 7.11141, 6.22101, 6.16544),
            (6.84118, 7.08432, 7.59844, 7.08229, 7.26774, 7.24991),
            (9.45215, 10.6943, 8.64719, 10.1592, 7.75044, 8.78615),
            (7.04737, 6.87185, 7.58586, 6.92456, 6.84243, 7.36913)]
        self.assertEqual(
            cluster_traits(traits_data_list),
            ((0.0, 0.20337048635536847, 0.16381088984330505, 1.7388553629398245,
              1.5025235756329178, 0.6952839500255574, 1.271661230252733,
              0.2100487290977544, 1.4699690641062024, 0.7934461515867415),
             (0.20337048635536847, 0.0, 0.2198321044997198, 1.5753041735592204,
              1.4815755944537086, 0.26087293140686374, 1.6939790104301427,
              0.06024619831474998, 1.7430082449189215, 0.4497104244247795),
             (0.16381088984330505, 0.2198321044997198, 0.0, 1.9073926868549234,
              1.0396738891139845, 0.5278328671176757, 1.6275069061182947,
              0.2636503792482082, 1.739617877037615, 0.7127042590637039),
             (1.7388553629398245, 1.5753041735592204, 1.9073926868549234, 0.0,
              0.9936846292920328, 1.1169999189889366, 0.6007483980555253,
              1.430209221053372, 0.25879514152086425, 0.9313185954797953),
             (1.5025235756329178, 1.4815755944537086, 1.0396738891139845,
              0.9936846292920328, 0.0, 1.027827186339337, 1.1441743109173244,
              1.4122477962364253, 0.8968250491499363, 1.1683723389247052),
             (0.6952839500255574, 0.26087293140686374, 0.5278328671176757,
              1.1169999189889366, 1.027827186339337, 0.0, 1.8420471110023269,
              0.19179284676938602, 1.4875072385631605, 0.23451785425383564),
             (1.271661230252733, 1.6939790104301427, 1.6275069061182947,
              0.6007483980555253, 1.1441743109173244, 1.8420471110023269, 0.0,
              1.6540234785929928, 0.2140799896286565, 1.7413442197913358),
             (0.2100487290977544, 0.06024619831474998, 0.2636503792482082,
              1.430209221053372, 1.4122477962364253, 0.19179284676938602,
              1.6540234785929928, 0.0, 1.5225640692832796, 0.33370067057028485),
             (1.4699690641062024, 1.7430082449189215, 1.739617877037615,
              0.25879514152086425, 0.8968250491499363, 1.4875072385631605,
              0.2140799896286565, 1.5225640692832796, 0.0, 1.3256191648260216),
             (0.7934461515867415, 0.4497104244247795, 0.7127042590637039,
              0.9313185954797953, 1.1683723389247052, 0.23451785425383564,
              1.7413442197913358, 0.33370067057028485, 1.3256191648260216,
              0.0)))

    def test_compute_heatmap_order(self):
        """Test the orders."""
        self.assertEqual(
            compute_traits_order(slinked), (0, 2, 1, 7, 5, 9, 3, 6, 8, 4))

    def test_retrieve_strains_and_values(self):
        """Test retrieval of strains and values."""
        for orders, slist, tdata, expected in [
                [
                    [2],
                    ["s1", "s2", "s3", "s4"],
                    [[2, 9, 6, None, 4],
                     [7, 5, None, None, 4],
                     [9, None, 5, 4, 7],
                     [6, None, None, 4, None]],
                    [[2, ["s1", "s3", "s4"], [9, 5, 4]]]
                ],
                [
                    [3],
                    ["s1", "s2", "s3", "s4", "s5"],
                    [[2, 9, 6, None, 4],
                     [7, 5, None, None, 4],
                     [9, None, 5, 4, 7],
                     [6, None, None, 4, None]],
                    [[3, ["s1", "s4"], [6, 4]]]
                ]]:
            with self.subTest(strainlist=slist, traitdata=tdata):
                self.assertEqual(
                    retrieve_strains_and_values(orders, slist, tdata), expected)

    def test_get_lrs_from_chr(self):
        for trait, chromosome, expected in [
                [{"chromosomes": {}}, 3, [None]],
                [{"chromosomes": {3: {"loci": [
                    {"Locus": "b", "LRS": 1.9},
                    {"Locus": "a", "LRS": 13.2},
                    {"Locus": "d", "LRS": 53.21},
                    {"Locus": "c", "LRS": 2.22}]}}},
                 3,
                 [13.2, 1.9, 2.22, 53.21]]]:
            with self.subTest(trait=trait, chromosome=chromosome):
                self.assertEqual(get_lrs_from_chr(trait, chromosome), expected)
