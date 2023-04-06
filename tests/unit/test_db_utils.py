"""module contains test for db_utils"""
from unittest import mock

import pytest

import gn3
from gn3.db_utils import parse_db_url, database_connection

@pytest.mark.unit_test
@mock.patch("gn3.db_utils.mdb")
@mock.patch("gn3.db_utils.parse_db_url")
def test_database_connection(mock_db_parser, mock_sql):
    """test for creating database connection"""
    print(f"MOCK SQL: {mock_sql}")
    print(f"MOCK DB PARSER: {mock_db_parser}")
    mock_db_parser.return_value = ("localhost", "guest", "4321", "users", None)

    with database_connection("mysql://guest:4321@localhost/users") as conn:
        mock_sql.connect.assert_called_with(
            db="users", user="guest", passwd="4321", host="localhost",
            port=3306)

@pytest.mark.unit_test
def test_parse_db_url():
    """test for parsing db_uri env variable"""
    results = parse_db_url("mysql://username:4321@localhost/test")
    expected_results = ("localhost", "username", "4321", "test", None)
    assert results == expected_results
