"""This contains unit-tests for gn3.computations.diff"""
import unittest
import os

from gn3.computations.diff import generate_diff

TESTDIFF = """3,4c3,4
< C57BL/6J,x,x,x
< BXD1,18.700,x,x
---
> C57BL/6J,19.000,x,x
> BXD1,15.700,x,x
6c6
< BXD11,18.900,x,x
---
> BXD11,x,x,x
"""


class TestDiff(unittest.TestCase):
    """Test cases for computations.diff"""
    def test_generate_diff(self):
        """Test that the correct diff is generated"""
        data = os.path.join(os.path.dirname(__file__).split("unit")[0],
                            "test_data/trait_data_10007.csv")
        edited_data = os.path.join(os.path.dirname(__file__).split("unit")[0],
                                   "test_data/edited_trait_data_10007.csv")
        self.assertEqual(generate_diff(data, edited_data), TESTDIFF)
