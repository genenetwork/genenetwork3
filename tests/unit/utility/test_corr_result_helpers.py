""" Test correlation helper methods """

import unittest
from gn3.utility.corr_result_helpers import normalize_values
from gn3.utility.corr_result_helpers import common_keys
from gn3.utility.corr_result_helpers import normalize_values_with_samples


class TestCorrelationHelpers(unittest.TestCase):
    """Test methods for normalising lists"""

    def test_normalize_values(self):
        """Test that a list is normalised correctly"""
        self.assertEqual(
            normalize_values([2.3, None, None, 3.2, 4.1, 5],\
                [3.4, 7.2, 1.3, None, 6.2, 4.1]),
            ([2.3, 4.1, 5], [3.4, 6.2, 4.1], 3)
        )

    def test_common_keys(self):
        """Test that common keys are returned as a list"""
        test_a = dict(BXD1=9.113, BXD2=9.825, BXD14=8.985, BXD15=9.300)
        test_b = dict(BXD1=9.723, BXD3=9.825, BXD14=9.124, BXD16=9.300)
        self.assertEqual(sorted(common_keys(test_a, test_b)),
                         ['BXD1', 'BXD14'])

    def test_normalize_values_with_samples(self):
        """Test that a sample(dict) is normalised correctly"""
        self.assertEqual(
            normalize_values_with_samples(
                dict(BXD1=9.113, BXD2=9.825, BXD14=8.985,
                     BXD15=9.300, BXD20=9.300),
                dict(BXD1=9.723, BXD3=9.825, BXD14=9.124, BXD16=9.300)),
            (({'BXD1': 9.113, 'BXD14': 8.985}, {'BXD1': 9.723, 'BXD14': 9.124}, 2))
        )
