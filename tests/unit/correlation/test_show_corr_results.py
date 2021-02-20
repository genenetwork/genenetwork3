"""module contains code for testing creating show correlation object"""

import unittest
from gn3.correlation.show_corr_results import CorrelationResults


class TestCorrelationResults(unittest.TestCase):
	def test_for_assertion(self):
		with self.assertRaises(AssertionError):
			corr_results_object = CorrelationResults(start_vars={})


	def test_for_do_correlation(self):

		start_vars = {
		  "corr_type":"sample",
		  "corr_sample_method":"pearson",
		  "corr_dataset":"HC_M2_0606_P",
		  "corr_return_results":100
		}

		corr_results_object = CorrelationResults(start_vars=start_vars)

		results = corr_results_object.do_correlation()
		self.assertEqual(results,{
    	 "success":"data"
    	})


		# no assertionError

		
