"""module contains test for db_utils"""
import pytest

from gn3.db_utils import parse_db_url


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "sql_uri,expected",
    (("mysql://theuser:passwd@thehost:3306/thedb",
      {
          "host": "thehost",
          "port": 3306,
          "user": "theuser",
          "password": "passwd",
          "database": "thedb"
      }),
     (("mysql://auser:passwd@somehost:3307/thedb?"
       "unix_socket=/run/mysqld/mysqld.sock&connect_timeout=30"),
      {
          "host": "somehost",
          "port": 3307,
          "user": "auser",
          "password": "passwd",
          "database": "thedb",
          "unix_socket": "/run/mysqld/mysqld.sock",
          "connect_timeout": 30
      }),
     ("mysql://guest:4321@localhost/users",
      {
          "host": "localhost",
          "port": 3306,
          "user": "guest",
          "password": "4321",
          "database": "users"
      }),
     ("mysql://localhost/users",
      {
          "host": "localhost",
          "port": 3306,
          "user": None,
          "password": None,
          "database": "users"
      })))
def test_parse_db_url(sql_uri, expected):
    """Test that valid URIs are passed into valid connection dicts"""
    assert parse_db_url(sql_uri) == expected


@pytest.mark.unit_test
@pytest.mark.parametrize(
    "sql_uri,invalidopt",
    (("mysql://localhost/users?socket=/run/mysqld/mysqld.sock", "socket"),
     ("mysql://localhost/users?connect_timeout=30&notavalidoption=value",
      "notavalidoption")))
def test_parse_db_url_with_invalid_options(sql_uri, invalidopt):
    """Test that invalid options cause the function to raise an exception."""
    with pytest.raises(AssertionError) as exc_info:
        parse_db_url(sql_uri)

    assert exc_info.value.args[0] == f"Invalid database connection option ({invalidopt}) provided."
