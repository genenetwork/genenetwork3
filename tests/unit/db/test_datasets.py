"""Tests for gn3/db/datasets.py"""

from unittest import mock, TestCase
import pytest
from gn3.db.datasets import (
    retrieve_dataset_name,
    retrieve_group_fields,
    retrieve_geno_group_fields,
    retrieve_publish_group_fields,
    retrieve_probeset_group_fields)

class TestDatasetsDBFunctions(TestCase):
    """Test cases for datasets functions."""

    @pytest.mark.unit_test
    def test_retrieve_dataset_name(self):
        """Test that the function is called correctly."""
        for trait_type, thresh, trait_name, dataset_name, columns, table, expected in [
                ["ProbeSet", 9, "probesetTraitName", "probesetDatasetName",
                 "Id, Name, FullName, ShortName, DataScale", "ProbeSetFreeze",
                 {"dataset_id": None, "dataset_name": "probesetDatasetName",
                  "dataset_fullname": "probesetDatasetName"}],
                ["Geno", 3, "genoTraitName", "genoDatasetName",
                 "Id, Name, FullName, ShortName", "GenoFreeze", {}],
                ["Publish", 6, "publishTraitName", "publishDatasetName",
                 "Id, Name, FullName, ShortName", "PublishFreeze", {}]]:
            db_mock = mock.MagicMock()
            with self.subTest(trait_type=trait_type):
                with db_mock.cursor() as cursor:
                    cursor.fetchone.return_value = {}
                    self.assertEqual(
                        retrieve_dataset_name(
                            trait_type, thresh, trait_name, dataset_name, db_mock),
                        expected)
                    cursor.execute.assert_called_once_with(
                        "SELECT {cols} "
                        "FROM {table} "
                        "WHERE public > %(threshold)s AND "
                        "(Name = %(name)s "
                        "OR FullName = %(name)s "
                        "OR ShortName = %(name)s)".format(
                            table=table, cols=columns),
                        {"threshold": thresh, "name": dataset_name})

    @pytest.mark.unit_test
    def test_retrieve_probeset_group_fields(self):
        """
        Test that the `group` and `group_id` fields are retrieved appropriately
        for the 'ProbeSet' trait type.
        """
        for trait_name, expected in [
                ["testProbeSetName", {}]]:
            db_mock = mock.MagicMock()
            with self.subTest(trait_name=trait_name, expected=expected):
                with db_mock.cursor() as cursor:
                    cursor.execute.return_value = ()
                    self.assertEqual(
                        retrieve_probeset_group_fields(trait_name, db_mock),
                        expected)
                    cursor.execute.assert_called_once_with(
                        (
                            "SELECT InbredSet.Name, InbredSet.Id"
                            " FROM InbredSet, ProbeSetFreeze, ProbeFreeze"
                            " WHERE ProbeFreeze.InbredSetId = InbredSet.Id"
                            " AND ProbeFreeze.Id = ProbeSetFreeze.ProbeFreezeId"
                            " AND ProbeSetFreeze.Name = %(name)s"),
                        {"name": trait_name})

    @pytest.mark.unit_test
    def test_retrieve_group_fields(self):
        """
        Test that the group fields are set up correctly for the different trait
        types.
        """
        for trait_type, trait_name, dataset_info, expected in [
                ["Publish", "pubTraitName01", {"dataset_name": "pubDBName01"},
                 {"dataset_name": "pubDBName01", "group": ""}],
                ["ProbeSet", "prbTraitName01", {"dataset_name": "prbDBName01"},
                 {"dataset_name": "prbDBName01", "group": ""}],
                ["Geno", "genoTraitName01", {"dataset_name": "genoDBName01"},
                 {"dataset_name": "genoDBName01", "group": ""}],
                ["Temp", "tempTraitName01", {}, {"group": ""}],
                ]:
            db_mock = mock.MagicMock()
            with self.subTest(
                    trait_type=trait_type, trait_name=trait_name,
                    dataset_info=dataset_info):
                with db_mock.cursor() as cursor:
                    cursor.execute.return_value = ("group_name", 0)
                    self.assertEqual(
                        retrieve_group_fields(
                            trait_type, trait_name, dataset_info, db_mock),
                        expected)

    @pytest.mark.unit_test
    def test_retrieve_publish_group_fields(self):
        """
        Test that the `group` and `group_id` fields are retrieved appropriately
        for the 'Publish' trait type.
        """
        for trait_name, expected in [
                ["testPublishName", {}]]:
            db_mock = mock.MagicMock()
            with self.subTest(trait_name=trait_name, expected=expected):
                with db_mock.cursor() as cursor:
                    cursor.execute.return_value = ()
                    self.assertEqual(
                        retrieve_publish_group_fields(trait_name, db_mock),
                        expected)
                    cursor.execute.assert_called_once_with(
                        (
                            "SELECT InbredSet.Name, InbredSet.Id"
                            " FROM InbredSet, PublishFreeze"
                            " WHERE PublishFreeze.InbredSetId = InbredSet.Id"
                            " AND PublishFreeze.Name = %(name)s"),
                        {"name": trait_name})

    @pytest.mark.unit_test
    def test_retrieve_geno_group_fields(self):
        """
        Test that the `group` and `group_id` fields are retrieved appropriately
        for the 'Geno' trait type.
        """
        for trait_name, expected in [
                ["testGenoName", {}]]:
            db_mock = mock.MagicMock()
            with self.subTest(trait_name=trait_name, expected=expected):
                with db_mock.cursor() as cursor:
                    cursor.execute.return_value = ()
                    self.assertEqual(
                        retrieve_geno_group_fields(trait_name, db_mock),
                        expected)
                    cursor.execute.assert_called_once_with(
                        (
                            "SELECT InbredSet.Name, InbredSet.Id"
                            " FROM InbredSet, GenoFreeze"
                            " WHERE GenoFreeze.InbredSetId = InbredSet.Id"
                            " AND GenoFreeze.Name = %(name)s"),
                        {"name": trait_name})
