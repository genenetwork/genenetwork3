"""module contains test for db_utils"""

from unittest import TestCase
from unittest import mock

from types import SimpleNamespace

from gn3.db_utils import database_connector
from gn3.db_utils import parse_db_url


class TestDatabase(TestCase):
    """class contains testd for db connection functions"""

    @mock.patch("gn3.db_utils.mdb")
    @mock.patch("gn3.db_utils.parse_db_url")
    def test_database_connector(self, mock_db_parser, mock_sql):
        """test for creating database connection"""
        mock_db_parser.return_value = ("localhost", "guest", "4321", "users")
        callable_cursor = lambda: SimpleNamespace(execute=3)
        cursor_object = SimpleNamespace(cursor=callable_cursor)
        mock_sql.connect.return_value = cursor_object
        mock_sql.close.return_value = None
        results = database_connector()

        mock_sql.connect.assert_called_with(
            "localhost", "guest", "4321", "users")
        self.assertIsInstance(
            results, tuple, "database not created successfully")

    @mock.patch("gn3.db_utils.SQL_URI",
                "mysql://username:4321@localhost/test")
    def test_parse_db_url(self):
        """test for parsing db_uri env variable"""
        results = parse_db_url()
        expected_results = ("localhost", "username", "4321", "test")
        self.assertEqual(results, expected_results)
