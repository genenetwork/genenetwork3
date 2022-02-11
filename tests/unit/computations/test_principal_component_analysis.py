"""module contains unittests for pca"""
import unittest

from gn3.computations.principal_component_analysis import compute_zscores
from numpy.testing import assert_allclose


class TestPCA(unittest.TestCase):
    """pca testcase class"""

    def test_compute_zscores(self):

        for test_array, axis, ddof, expected in [([0.7972,  0.0767,  0.4383,  0.7866,  0.8091,
                                                   0.1954,  0.6307,  0.6599,  0.1065,  0.0508], 0, 0,
                                                  [1.1273, -1.247, -0.0552,  1.0923,  1.1664, -0.8559,  0.5786, 0.6748, -1.1488, -1.3324])]:
            with self.subTest(nums=test_array, axis=axis, ddof=ddof):

                assert_allclose(
                    compute_zscores(test_array, axis, ddof), expected)
