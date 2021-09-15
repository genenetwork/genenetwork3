"""module contains python code for wgcna"""
from unittest import TestCase


def compute_sum(rhs_val, lhs_val):
    """function to compute sum of two numbers"""
    return rhs_val+lhs_val


class TestWgcna(TestCase):
    """test class for wgcna"""

    def test_compute_sum(self):
        """test for compute sum function"""
        self.assertEqual(compute_sum(1, 2), 3)
