"""Tests for gn3/db/traits.py"""
from unittest import mock, TestCase
from gn3.db.traits import retrieve_probeset_trait_name

class TestTraitsDBFunctions(TestCase):
    "Test cases for traits functions"

    def test_retrieve_probeset_trait_name(self):
        """Test that the function is called correctly."""
        db_mock = mock.MagicMock()
        with db_mock.cursor() as cursor:
            cursor.fetchone.return_value = (
                "testName", "testNameFull", "testNameShort", "dataScale")
            self.assertEqual(
                retrieve_probeset_trait_name(9, "testName", db_mock),
                ("testName", "testNameFull", "testNameShort", "dataScale"))
            cursor.execute.assert_called_once_with(
                "SELECT Id, Name, FullName, ShortName, DataScale "
                "FROM ProbeSetFreeze "
                "WHERE public > %(threshold)s AND "
                "(Name = %(name)s OR FullName = %(name)s OR ShortName = %(name)s)",
                {"threshold": 9, "name": "testName"})
