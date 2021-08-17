"""Module contains tests for gn3.computations.heatmap"""
from unittest import TestCase
from gn3.computations.heatmap import export_trait_data

strainlist = ["B6cC3-1", "BXD1", "BXD12", "BXD16", "BXD19", "BXD2"]
trait_data = {"mysqlid": 36688172, "data": {"B6cC3-1": {"strain_name": "B6cC3-1", "value": 7.51879, "variance": None, "ndata": None}, "BXD1": {"strain_name": "BXD1", "value": 7.77141, "variance": None, "ndata": None}, "BXD12": {"strain_name": "BXD12", "value": 8.39265, "variance": None, "ndata": None}, "BXD16": {"strain_name": "BXD16", "value": 8.17443, "variance": None, "ndata": None}, "BXD19": {"strain_name": "BXD19", "value": 8.30401, "variance": None, "ndata": None}, "BXD2": {"strain_name": "BXD2", "value": 7.80944, "variance": None, "ndata": None}, "BXD21": {"strain_name": "BXD21", "value": 8.93809, "variance": None, "ndata": None}, "BXD24": {"strain_name": "BXD24", "value": 7.99415, "variance": None, "ndata": None}, "BXD27": {"strain_name": "BXD27", "value": 8.12177, "variance": None, "ndata": None}, "BXD28": {"strain_name": "BXD28", "value": 7.67688, "variance": None, "ndata": None}, "BXD32": {"strain_name": "BXD32", "value": 7.79062, "variance": None, "ndata": None}, "BXD39": {"strain_name": "BXD39", "value": 8.27641, "variance": None, "ndata": None}, "BXD40": {"strain_name": "BXD40", "value": 8.18012, "variance": None, "ndata": None}, "BXD42": {"strain_name": "BXD42", "value": 7.82433, "variance": None, "ndata": None}, "BXD6": {"strain_name": "BXD6", "value": 8.09718, "variance": None, "ndata": None}, "BXH14": {"strain_name": "BXH14", "value": 7.97475, "variance": None, "ndata": None}, "BXH19": {"strain_name": "BXH19", "value": 7.67223, "variance": None, "ndata": None}, "BXH2": {"strain_name": "BXH2", "value": 7.93622, "variance": None, "ndata": None}, "BXH22": {"strain_name": "BXH22", "value": 7.43692, "variance": None, "ndata": None}, "BXH4": {"strain_name": "BXH4", "value": 7.96336, "variance": None, "ndata": None}, "BXH6": {"strain_name": "BXH6", "value": 7.75132, "variance": None, "ndata": None}, "BXH7": {"strain_name": "BXH7", "value": 8.12927, "variance": None, "ndata": None}, "BXH8": {"strain_name": "BXH8", "value": 6.77338, "variance": None, "ndata": None}, "BXH9": {"strain_name": "BXH9", "value": 8.03836, "variance": None, "ndata": None}, "C3H/HeJ": {"strain_name": "C3H/HeJ", "value": 7.42795, "variance": None, "ndata": None}, "C57BL/6J": {"strain_name": "C57BL/6J", "value": 7.50606, "variance": None, "ndata": None}, "DBA/2J": {"strain_name": "DBA/2J", "value": 7.72588, "variance": None, "ndata": None}}}

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
                ["val", False, False, (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["val", False, True, (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["val", True, False, (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["val", True, True, (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["var", False, False, (None, None, None, None, None, None)],
                ["var", False, True, (None, None, None, None, None, None)],
                ["var", True, False, (None, None, None, None, None, None)],
                ["var", True, True, (None, None, None, None, None, None)],
                ["N", False, False, (None, None, None, None, None, None)],
                ["N", False, True, (None, None, None, None, None, None)],
                ["N", True, False, (None, None, None, None, None, None)],
                ["N", True, True, (None, None, None, None, None, None)],
                ["all", False, False, (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944)],
                ["all", False, True, (7.51879, None, 7.77141, None, 8.39265, None, 8.17443, None, 8.30401, None, 7.80944, None)],
                ["all", True, False, (7.51879, None, 7.77141, None, 8.39265, None, 8.17443, None, 8.30401, None, 7.80944, None)],
                ["all", True, True, (7.51879, None, None, 7.77141, None, None, 8.39265, None, None, 8.17443, None, None, 8.30401, None, None, 7.80944, None, None)]
        ]:
            with self.subTest(dtype=dtype, vflag=vflag, nflag=nflag):
                self.assertEqual(
                    export_trait_data(
                        trait_data, strainlist, dtype=dtype, var_exists=vflag,
                        n_exists=nflag),
                    expected)
