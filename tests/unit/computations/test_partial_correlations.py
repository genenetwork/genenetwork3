"""Module contains tests for gn3.partial_correlations"""

from unittest import TestCase

import pandas
import pytest
from numpy.testing import assert_allclose

from gn3.computations.partial_correlations import (
    fix_samples,
    control_samples,
    build_data_frame,
    tissue_correlation,
    find_identical_traits,
    good_dataset_samples_indexes)

sampleslist = ["B6cC3-1", "BXD1", "BXD12", "BXD16", "BXD19", "BXD2"]
control_traits = (
    {
        "mysqlid": 36688172,
        "data": {
            "B6cC3-1": {
                "sample_name": "B6cC3-1", "value": 7.51879, "variance": None,
                "ndata": None},
            "BXD1": {
                "sample_name": "BXD1", "value": 7.77141, "variance": None,
                "ndata": None},
            "BXD12": {
                "sample_name": "BXD12", "value": 8.39265, "variance": None,
                "ndata": None},
            "BXD16": {
                "sample_name": "BXD16", "value": 8.17443, "variance": None,
                "ndata": None},
            "BXD19": {
                "sample_name": "BXD19", "value": 8.30401, "variance": None,
                "ndata": None},
            "BXD2": {
                "sample_name": "BXD2", "value": 7.80944, "variance": None,
                "ndata": None}}},
    {
        "mysqlid": 36688172,
        "data": {
            "B6cC3-21": {
                "sample_name": "B6cC3-1", "value": 7.51879, "variance": None,
                "ndata": None},
            "BXD21": {
                "sample_name": "BXD1", "value": 7.77141, "variance": None,
                "ndata": None},
            "BXD12": {
                "sample_name": "BXD12", "value": 8.39265, "variance": None,
                "ndata": None},
            "BXD16": {
                "sample_name": "BXD16", "value": 8.17443, "variance": None,
                "ndata": None},
            "BXD19": {
                "sample_name": "BXD19", "value": 8.30401, "variance": None,
                "ndata": None},
            "BXD2": {
                "sample_name": "BXD2", "value": 7.80944, "variance": None,
                "ndata": None}}},
    {
        "mysqlid": 36688172,
        "data": {
            "B6cC3-1": {
                "sample_name": "B6cC3-1", "value": 7.51879, "variance": None,
                "ndata": None},
            "BXD1": {
                "sample_name": "BXD1", "value": 7.77141, "variance": None,
                "ndata": None},
            "BXD12": {
                "sample_name": "BXD12", "value": None, "variance": None,
                "ndata": None},
            "BXD16": {
                "sample_name": "BXD16", "value": None, "variance": None,
                "ndata": None},
            "BXD19": {
                "sample_name": "BXD19", "value": None, "variance": None,
                "ndata": None},
            "BXD2": {
                "sample_name": "BXD2", "value": 7.80944, "variance": None,
                "ndata": None}}})

dictified_control_samples = (
    {"B6cC3-1": {"sample_name": "B6cC3-1", "value": 7.51879, "variance": None},
     "BXD1": {"sample_name": "BXD1", "value": 7.77141, "variance": None},
     "BXD12": {"sample_name": "BXD12", "value": 8.39265, "variance": None},
     "BXD16": {"sample_name": "BXD16", "value": 8.17443, "variance": None},
     "BXD19": {"sample_name": "BXD19", "value": 8.30401, "variance": None},
     "BXD2": {"sample_name": "BXD2", "value": 7.80944, "variance": None}},
    {"BXD12": {"sample_name": "BXD12", "value": 8.39265, "variance": None},
     "BXD16": {"sample_name": "BXD16", "value": 8.17443, "variance": None},
     "BXD19": {"sample_name": "BXD19", "value": 8.30401, "variance": None},
     "BXD2": {"sample_name": "BXD2", "value": 7.80944, "variance": None}},
    {"B6cC3-1": {"sample_name": "B6cC3-1", "value": 7.51879, "variance": None},
     "BXD1": {"sample_name": "BXD1", "value": 7.77141, "variance": None},
     "BXD2": {"sample_name": "BXD2", "value":  7.80944, "variance": None}})

class TestPartialCorrelations(TestCase):
    """Class for testing partial correlations computation functions"""

    @pytest.mark.unit_test
    def test_control_samples(self):
        """Test that the control_samples works as expected."""
        self.assertEqual(
            control_samples(control_traits, sampleslist),
            ((("B6cC3-1", "BXD1", "BXD12", "BXD16", "BXD19", "BXD2"),
              ("BXD12", "BXD16", "BXD19", "BXD2"),
              ("B6cC3-1", "BXD1", "BXD2")),
             ((7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944),
              (8.39265, 8.17443, 8.30401, 7.80944),
              (7.51879, 7.77141, 7.80944)),
             ((None, None, None, None, None, None), (None, None, None, None),
              (None, None, None)),
             (6, 4, 3)))

    @pytest.mark.unit_test
    def test_fix_samples(self):
        """
        Test that `fix_samples` returns only the common samples

        Given:
            - A primary trait
            - A sequence of control samples
        When:
            - The two arguments are passed to `fix_samples`
        Then:
            - Only the names of the samples present in the primary trait that
              are also present in ALL the control traits are present in the
              return value
            - Only the values of the samples present in the primary trait that
              are also present in ALL the control traits are present in the
              return value
            - ALL the values for ALL the control traits are present in the
              return value
            - Only the variances of the samples present in the primary trait
              that are also present in ALL the control traits are present in the
              return value
            - ALL the variances for ALL the control traits are present in the
              return value
            - The return value is a tuple of the above items, in the following
              order:
                ((sample_names, ...), (primary_trait_values, ...),
                 (control_traits_values, ...), (primary_trait_variances, ...)
                 (control_traits_variances, ...))
        """
        self.assertEqual(
            fix_samples(
                {"B6cC3-1": {"sample_name": "B6cC3-1", "value": 7.51879,
                             "variance": None},
                 "BXD1": {"sample_name": "BXD1", "value": 7.77141,
                          "variance": None},
                 "BXD2": {"sample_name": "BXD2", "value":  7.80944,
                          "variance": None}},
                dictified_control_samples),
            (("BXD2",), (7.80944,),
             (7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944, 8.39265,
              8.17443, 8.30401, 7.80944, 7.51879, 7.77141, 7.80944),
             (None,),
             (None, None, None, None, None, None, None, None, None, None, None,
              None, None)))

    @pytest.mark.unit_test
    def test_find_identical_traits(self):
        """
        Test `gn3.partial_correlations.find_identical_traits`.

        Given:
            - the name of a primary trait
            - a sequence of values for the primary trait
            - a sequence of names of control traits
            - a sequence of values of control traits
        When:
            - the arguments above are passed to the `find_identical_traits`
              function
        Then:
            - Return ALL trait names that have the same value when up to three
              decimal places are considered
        """
        for primn, primv, contn, contv, expected in (
                ("pt", (12.98395,), ("ct0", "ct1", "ct2"),
                 ((0.1234, 2.3456, 3.4567),), tuple()),
                ("pt", (12.98395, 2.3456, 3.4567), ("ct0", "ct1", "ct2"),
                 ((12.98354, 2.3456, 3.4567), (64.2334, 6.3256, 64.2364),
                  (4.2374, 67.2345, 7.48234)), ("pt", "ct0")),
                ("pt", (12.98395, 75.52382), ("ct0", "ct1", "ct2", "ct3"),
                 ((0.1234, 2.3456), (0.3621, 6543.572), (0.1234, 2.3456),
                  (0.1233, 4.5678)), ("ct0", "ct2"))
        ):
            with self.subTest(
                    primary_name=primn, primary_value=primv,
                    control_names=contn, control_values=contv):
                self.assertEqual(
                    find_identical_traits(primn, primv, contn, contv), expected)

    @pytest.mark.unit_test
    def test_tissue_correlation_error(self):
        """
        Test that `tissue_correlation` raises specific exceptions for particular
        error conditions.
        """
        for primary, target, method, error, error_msg in (
                ((1, 2, 3), (4, 5, 6, 7), "pearson",
                 AssertionError,
                 (
                     "The lengths of the `primary_trait_values` and "
                     "`target_trait_values` must be equal")),
                ((1, 2, 3), (4, 5, 6, 7), "spearman",
                 AssertionError,
                 (
                     "The lengths of the `primary_trait_values` and "
                     "`target_trait_values` must be equal")),
                ((1, 2, 3, 4), (5, 6, 7), "pearson",
                 AssertionError,
                 (
                     "The lengths of the `primary_trait_values` and "
                     "`target_trait_values` must be equal")),
                ((1, 2, 3, 4), (5, 6, 7), "spearman",
                 AssertionError,
                 (
                     "The lengths of the `primary_trait_values` and "
                     "`target_trait_values` must be equal")),
                ((1, 2, 3), (4, 5, 6), "nonexistentmethod",
                 AssertionError,
                 (
                     "Method must be one of: pearson, spearman"))):
            with self.subTest(primary=primary, target=target, method=method):
                with self.assertRaises(error, msg=error_msg):
                    tissue_correlation(primary, target, method)

    @pytest.mark.unit_test
    def test_tissue_correlation(self): # pylint: disable=R0201
        """
        Test that the correct correlation values are computed for the given:
        - primary trait
        - target trait
        - method
        """
        for primary, target, method, expected in (
                ((12.34, 18.36, 42.51), (37.25, 46.25, 46.56), "pearson",
                 (0.6761779252651052, 0.5272701133657985)),
                ((1, 2, 3, 4, 5), (5, 6, 7, 8, 7), "spearman",
                 (0.8207826816681233, 0.08858700531354381))):
            with self.subTest(primary=primary, target=target, method=method):
                assert_allclose(
                    tissue_correlation(primary, target, method), expected)

    @pytest.mark.unit_test
    def test_good_dataset_samples_indexes(self):
        """
        Test that `good_dataset_samples_indexes` returns correct indices.
        """
        self.assertEqual(
            good_dataset_samples_indexes(
                ("a", "e", "i", "k"),
                ("a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l")),
            (0, 4, 8, 10))

    @pytest.mark.unit_test
    def test_build_data_frame(self):
        """
        Check that the function builds the correct data frame.
        """
        for xdata, ydata, zdata, expected in (
                ((0.1, 1.1, 2.1), (2.1, 3.1, 4.1), (5.1, 6.1, 7.1),
                 pandas.DataFrame({
                     "x": (0.1, 1.1, 2.1), "y": (2.1, 3.1, 4.1),
                     "z": (5.1, 6.1, 7.1)})),
                ((0.1, 1.1, 2.1), (2.1, 3.1, 4.1),
                 ((5.1, 6.1, 7.1), (5.2, 6.2, 7.2), (5.3, 6.3, 7.3)),
                 pandas.DataFrame({
                     "x": (0.1, 1.1, 2.1), "y": (2.1, 3.1, 4.1),
                     "z0": (5.1, 6.1, 7.1), "z1": (5.2, 6.2, 7.2),
                     "z2": (5.3, 6.3, 7.3)}))):
            with self.subTest(xdata=xdata, ydata=ydata, zdata=zdata):
                self.assertTrue(
                    build_data_frame(xdata, ydata, zdata).equals(expected))
