"""Module that holds fixtures for integration tests"""
from pathlib import Path
import pytest
import MySQLdb

from gn3.app import create_app
from gn3.chancy import random_string
from gn3.db_utils import parse_db_url, database_connection


@pytest.fixture(scope="session")
def client():
    """Create a test client fixture for tests"""
    # Do some setup
    app = create_app({
        "TESTING": True,
        "LMDB_DATA_PATH": str(
            Path(__file__).parent.parent /
            Path("test_data/lmdb-test-data")
        ),
        "AUTH_SERVER_URL": "http://127.0.0.1:8081",
    })
    yield app.test_client()
    # Do some teardown/cleanup


@pytest.fixture(scope="session")
def db_conn(client):  # pylint: disable=[redefined-outer-name]
    """Create a db connection fixture for tests"""
    # 01) Generate random string to append to all test db artifacts for the session
    live_db_uri = client.application.config["SQL_URI"]
    rand_str = random_string(15)
    live_db_details = parse_db_url(live_db_uri)
    test_db_name = f"test_{live_db_details[3]}_{rand_str}"
    #
    # 02) Create new test db
    #     Use context manager to ensure the live connection is automatically
    #     closed on exit
    with database_connection(live_db_uri) as live_db_conn:
        with live_db_conn.cursor() as live_db_cursor:
            live_db_cursor.execute(f"CREATE DATABASE {test_db_name}")
            #
            # 03) Copy over table structure from source db into test db
            live_db_cursor.execute("SHOW TABLES;")
            queries = (
                f"CREATE TABLE {test_db_name}.{row[0]} AS SELECT * FROM {row[0]} WHERE 1=0;"
                for row in live_db_cursor.fetchall())
            for query in queries:
                live_db_cursor.execute(query)
            #
            # 04) get database connection to test db and yield it up
            test_db_conn = MySQLdb.connect(
                live_db_details[0], live_db_details[1], live_db_details[2],
                test_db_name)
            yield test_db_conn
            #
            # 05) Clean up after ourselves
            #   a.) Close the test db connection
            test_db_conn.close()
            #
            #   b.) Delete the test database
            live_db_cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
