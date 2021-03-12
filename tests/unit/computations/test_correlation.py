
import scipy
from unittest import TestCase
from gn3.computations.correlations import normalize_values


class TestSum(TestCase):

    def test_normalize_values(self):
        results = normalize_values([2.3, None, None, 3.2, 4.1, 5], [
                                   3.4, 7.2, 1.3, None, 6.2, 4.1])

        expected_results = ([2.3, 4.1, 5], [3.4, 6.2, 4.1], 3)

        self.assertEqual(results, expected_results)
