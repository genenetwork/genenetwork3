"""module contains test for db_utils"""

from unittest import TestCase
from gn3.db_utils import database_connector

class TestDatabase(TestCase):
    """class contains testd for db connection functions"""

    def test_fails(self):
        """initial test ;must fail"""
        self.assertEqual(3, 3)

    def test_database_connector(self):
        """test for creating database connection"""
        results = database_connector()

        self.assertIsInstance(
            results, tuple, "database not created successfully")
