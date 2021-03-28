"""module contains test for db_utils"""

from unittest import TestCase
from unittest import mock

from types import SimpleNamespace

from gn3.db_utils import database_connector
from gn3.db_utils import execute_sql_query


class TestDatabase(TestCase):
    """class contains testd for db connection functions"""

    @mock.patch("gn3.db_utils.mdb")
    def test_database_connector(self, mock_sql):
        """test for creating database connection"""
        results = database_connector()
        cursor_object = SimpleNamespace(cursor=SimpleNamespace(execute=3))
        mock_sql.connect.return_value = cursor_object
        mock_sql.close.return_value = None

        self.assertIsInstance(
            results, tuple, "database not created successfully")

    def test_execute_sql_query(self):
        """test for function that executes any sql\
        query and return results"""

        results = execute_sql_query()

        self.assertEqual(results, True)
