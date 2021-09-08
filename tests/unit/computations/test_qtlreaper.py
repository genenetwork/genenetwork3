"""Module contains tests for gn3.computations.qtlreaper"""
from unittest import TestCase
from gn3.computations.qtlreaper import (
    parse_reaper_main_results,
    organise_reaper_main_results,
    parse_reaper_permutation_results)

class TestQTLReaper(TestCase):
    """Class for testing qtlreaper interface functions."""

    def test_parse_reaper_main_results(self):
        """Test that the main results file is parsed correctly."""
        self.assertEqual(
            parse_reaper_main_results(
                "tests/unit/computations/data/qtlreaper/main_output_sample.txt"),
            [
                {
                    "ID": "T1", "Locus": "rs31443144", "Chr": "1", "cM": 1.500,
                    "Mb": 3.010, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs6269442", "Chr": "1", "cM": 1.500,
                    "Mb": 3.492, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs32285189", "Chr": "1", "cM": 1.630,
                    "Mb": 3.511, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs258367496", "Chr": "1", "cM": 1.630,
                    "Mb": 3.660, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs32430919", "Chr": "1", "cM": 1.750,
                    "Mb": 3.777, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs36251697", "Chr": "1", "cM": 1.880,
                    "Mb": 3.812, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs30658298", "Chr": "1", "cM": 2.010,
                    "Mb": 4.431, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs51852623", "Chr": "1", "cM": 2.010,
                    "Mb": 4.447, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs31879829", "Chr": "1", "cM": 2.140,
                    "Mb": 4.519, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs36742481", "Chr": "1", "cM": 2.140,
                    "Mb": 4.776, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                }
            ])

    def test_parse_reaper_permutation_results(self):
        """Test that the permutations results file is parsed correctly."""
        self.assertEqual(
            parse_reaper_permutation_results(
                "tests/unit/computations/data/qtlreaper/permu_output_sample.txt"),
            [4.44174, 5.03825, 5.08167, 5.18119, 5.18578, 5.24563, 5.24619,
             5.24619, 5.27961, 5.28228, 5.43903, 5.50188, 5.51694, 5.56830,
             5.63874, 5.71346, 5.71936, 5.74275, 5.76764, 5.79815, 5.81671,
             5.82775, 5.89659, 5.92117, 5.93396, 5.93396, 5.94957])

    def test_organise_reaper_main_results(self):
        self.assertEqual(
            organise_reaper_main_results([
                {
                    "ID": "T1", "Locus": "rs31443144", "Chr": 1, "cM": 1.500,
                    "Mb": 3.010, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs6269442", "Chr": 1, "cM": 1.500,
                    "Mb": 3.492, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs32285189", "Chr": 1, "cM": 1.630,
                    "Mb": 3.511, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs258367496", "Chr": 1, "cM": 1.630,
                    "Mb": 3.660, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs32430919", "Chr": 1, "cM": 1.750,
                    "Mb": 3.777, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs36251697", "Chr": 1, "cM": 1.880,
                    "Mb": 3.812, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs30658298", "Chr": 1, "cM": 2.010,
                    "Mb": 4.431, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs51852623", "Chr": 2, "cM": 2.010,
                    "Mb": 4.447, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs31879829", "Chr": 2, "cM": 2.140,
                    "Mb": 4.519, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                },
                {
                    "ID": "T1", "Locus": "rs36742481", "Chr": 2, "cM": 2.140,
                    "Mb": 4.776, "LRS": 0.500, "Additive": -0.074,
                    "pValue": 1.000
                }
            ]),
            {"T1": {"ID": "T1",
                    "chromosomes": {
                        1: {"Chr": 1,
                            "loci": [
                                {
                                    "Locus": "rs31443144",  "cM": 1.500, "Mb": 3.010,
                                    "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                                },
                                {
                                    "Locus": "rs6269442", "cM": 1.500, "Mb": 3.492,
                                    "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                                },
                                {
                                    "Locus": "rs32285189", "cM": 1.630, "Mb": 3.511,
                                    "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                                },
                                {
                                    "Locus": "rs258367496", "cM": 1.630, "Mb": 3.660,
                                    "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                                },
                                {
                                    "Locus": "rs32430919", "cM": 1.750, "Mb": 3.777,
                                    "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                                },
                                {
                                    "Locus": "rs36251697", "cM": 1.880, "Mb": 3.812,
                                    "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                                },
                                {
                                    "Locus": "rs30658298", "cM": 2.010, "Mb": 4.431,
                                    "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                                }]},
                        2: {"Chr": 2,
                            "loci": [
                                {
                                    "Locus": "rs51852623", "cM": 2.010, "Mb": 4.447,
                                    "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                                },
                                {
                                    "Locus": "rs31879829", "cM": 2.140, "Mb": 4.519,
                                    "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                                },
                                {
                                    "Locus": "rs36742481", "cM": 2.140, "Mb": 4.776,
                                    "LRS": 0.500, "Additive": -0.074, "pValue": 1.000
                                }]}}}})
