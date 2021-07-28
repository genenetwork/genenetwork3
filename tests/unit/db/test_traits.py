"""Tests for gn3/db/traits.py"""
from unittest import mock, TestCase
from gn3.db.traits import retrieve_type_trait_name

class TestTraitsDBFunctions(TestCase):
    "Test cases for traits functions"

    def test_retrieve_probeset_trait_name(self):
        """Test that the function is called correctly."""
        for trait_type, thresh, trait_name, columns in [
                ["ProbeSet", 9, "testName",
                 "Id, Name, FullName, ShortName, DataScale"],
                ["Geno", 3, "genoTraitName", "Id, Name, FullName, ShortName"],
                ["Publish", 6, "publishTraitName",
                 "Id, Name, FullName, ShortName"],
                ["Temp", 4, "tempTraitName", "Id, Name, FullName, ShortName"]]:
            db_mock = mock.MagicMock()
            with self.subTest(trait_type=trait_type):
                with db_mock.cursor() as cursor:
                    cursor.fetchone.return_value = (
                        "testName", "testNameFull", "testNameShort",
                        "dataScale")
                    self.assertEqual(
                        retrieve_type_trait_name(
                            trait_type, thresh, trait_name, db_mock),
                        ("testName", "testNameFull", "testNameShort",
                         "dataScale"))
                    cursor.execute.assert_called_once_with(
                        "SELECT {cols} "
                        "FROM {ttype}Freeze "
                        "WHERE public > %(threshold)s AND "
                        "(Name = %(name)s OR FullName = %(name)s OR ShortName = %(name)s)".format(
                            cols=columns, ttype=trait_type),
                        {"threshold": thresh, "name": trait_name})
