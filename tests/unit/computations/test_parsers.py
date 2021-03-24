"""Test cases for procedures defined in computations.parsers"""
import unittest
import os

from gn3.computations.parsers import parse_genofile


class TestParsers(unittest.TestCase):
    """Test cases for some various parsers"""

    def test_parse_genofile_without_existing_file(self):
        """Assert that an error is raised if the genotype file is absent"""
        self.assertRaises(FileNotFoundError, parse_genofile,
                          "/non-existent-file")

    def test_parse_genofile_with_existing_file(self):
        """Test that a genotype file is parsed correctly"""
        strains = ["bxd1", "bxd2"]
        genotypes = [
            {"chr": "1", "locus": "rs31443144",
             "cm": "1.50", "mb": "3.010274",
             "values": [-1, -1],
             "dicvalues": {'bxd1': -1, 'bxd2': -1}},
            {"chr": "2", "locus": "rs27644551",
             "cm": "93.26", "mb": "173.542999",
             "values": [1, 1],
             "dicvalues": {'bxd1': 1, 'bxd2': 1}},
            {"chr": "3", "locus": "rs31187985",
             "cm": "17.12", "mb": "41.921845",
             "values": [1, 1],
             "dicvalues": {'bxd1': 1, 'bxd2': 1}},
            {"chr": "4", "locus": "rs30254612",
             "cm": "2.15", "mb": "3.718812",
             "values": [-1, 1],
             "dicvalues": {'bxd1': -1, 'bxd2': 1}},
            {"chr": "5", "locus": "UNCHS047057",
             "cm": "3.10", "mb": "4.199559",
             "values": [-1, -1],
             "dicvalues": {'bxd1': -1, 'bxd2': -1}},
            {"chr": "X", "locus": "ChrXp_no_data",
             "cm": "1.40", "mb": "3.231738",
             "values": [1, -1],
             "dicvalues": {'bxd1': 1, 'bxd2': -1}},
            {"chr": "X", "locus": "Affy_17539964",
             "cm": "1.40", "mb": "7.947581",
             "values": [1, -1],
             "dicvalues": {'bxd1': 1, 'bxd2': -1}},
        ]
        test_genotype_file = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            "../test_data/genotype.txt"
        ))
        self.assertEqual(parse_genofile(
            test_genotype_file), (strains, genotypes))
