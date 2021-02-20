"""module contains code for testing creating show correlation object"""

import unittest
from gn3.correlation.show_corr_results import CorrelationResults


class TestCorrelationResults(unittest.TestCase):
	def test_for_assertion(self):
		with self.assertRaises(AssertionError):
			corr_results_object = CorrelationResults(start_vars={})

		
