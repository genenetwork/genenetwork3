"""Module contains tests for gn3.partial_correlations"""

from unittest import TestCase
from gn3.partial_correlations import export_informative

class TestPartialCorrelations(TestCase):
    """Class for testing partial correlations computation functions"""

    def test_export_informative(self):
        """Test that the function exports appropriate data."""
        for trait_data, inc_var, expected in [
                [{"data": {
                    "sample1": {
                        "sample_name": "sample1", "value": 9, "variance": None,
                        "ndata": 13
                    },
                    "sample2": {
                        "sample_name": "sample2", "value": 8, "variance": None,
                        "ndata": 13
                    },
                    "sample3": {
                        "sample_name": "sample3", "value": 7, "variance": None,
                        "ndata": 13
                    },
                    "sample4": {
                        "sample_name": "sample4", "value": 6, "variance": None,
                        "ndata": 13
                    },
                }}, 0, (
                    ("sample1", "sample2", "sample3", "sample4"), (9, 8, 7, 6),
                    (None, None, None, None))],
                [{"data": {
                    "sample1": {
                        "sample_name": "sample1", "value": 9, "variance": None,
                        "ndata": 13
                    },
                    "sample2": {
                        "sample_name": "sample2", "value": 8, "variance": None,
                        "ndata": 13
                    },
                    "sample3": {
                        "sample_name": "sample3", "value": None, "variance": None,
                        "ndata": 13
                    },
                    "sample4": {
                        "sample_name": "sample4", "value": 6, "variance": None,
                        "ndata": 13
                    },
                }}, 0, (
                    ("sample1", "sample2", "sample4"), (9, 8, 6),
                    (None, None, None))],
                [{"data": {
                    "sample1": {
                        "sample_name": "sample1", "value": 9, "variance": None,
                        "ndata": 13
                    },
                    "sample2": {
                        "sample_name": "sample2", "value": 8, "variance": None,
                        "ndata": 13
                    },
                    "sample3": {
                        "sample_name": "sample3", "value": 7, "variance": None,
                        "ndata": 13
                    },
                    "sample4": {
                        "sample_name": "sample4", "value": 6, "variance": None,
                        "ndata": 13
                    },
                }}, True, (tuple(), tuple(), tuple())],
                [{"data": {
                    "sample1": {
                        "sample_name": "sample1", "value": 9, "variance": None,
                        "ndata": 13
                    },
                    "sample2": {
                        "sample_name": "sample2", "value": 8, "variance": 0.657,
                        "ndata": 13
                    },
                    "sample3": {
                        "sample_name": "sample3", "value": 7, "variance": None,
                        "ndata": 13
                    },
                    "sample4": {
                        "sample_name": "sample4", "value": 6, "variance": None,
                        "ndata": 13
                    },
                }}, 0, (
                    ("sample1", "sample2", "sample3", "sample4"), (9, 8, 7, 6),
                    (None, 0.657, None, None))]]:
            with self.subTest(trait_data=trait_data):
                self.assertEqual(
                    export_informative(trait_data, inc_var), expected)
