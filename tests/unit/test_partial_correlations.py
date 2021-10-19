"""Module contains tests for gn3.partial_correlations"""

from unittest import TestCase
from gn3.partial_correlations import (
    fix_samples,
    control_samples,
    dictify_by_samples)

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

    def test_dictify_by_samples(self):
        """
        Given:
            a sequence of sequences with sample names, values and variances, as
            in the output of `gn3.partial_correlations.control_samples` or
            the output of `gn3.db.traits.export_informative`
        When:
            the sequence is passed as an argument into the
            `gn3.partial_correlations.dictify_by_sample`
        Then:
            return a sequence of dicts with keys being the values of the sample
            names, and each of who's values being sub-dicts with the keys
            'sample_name', 'value' and 'variance' whose values correspond to the
            values passed in.
        """
        self.assertEqual(
            dictify_by_samples(
                ((("B6cC3-1", "BXD1", "BXD12", "BXD16", "BXD19", "BXD2"),
                  ("BXD12", "BXD16", "BXD19", "BXD2"),
                  ("B6cC3-1", "BXD1", "BXD2")),
                 ((7.51879, 7.77141, 8.39265, 8.17443, 8.30401, 7.80944),
                  (8.39265, 8.17443, 8.30401, 7.80944),
                  (7.51879, 7.77141, 7.80944)),
                 ((None, None, None, None, None, None), (None, None, None, None),
                  (None, None, None)),
                 (6, 4, 3))),
            dictified_control_samples)

    def test_fix_samples(self):
        """Test that fix_samples fixes the values"""
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
