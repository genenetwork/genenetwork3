"""Module that holds fixtures for integration tests"""
import os
import re
import json
import pytest

from gn3.app import create_app
from gn3.settings import SQL_URI
from gn3.random import random_string
from gn3.db_utils import parse_db_url, database_connector

@pytest.fixture(scope="session")
def client():
    """Create a test client fixture for tests"""
    # Do some setup
    app = create_app()
    app.config.update({"TESTING": True})
    app.testing = True
    yield app.test_client()
    # Do some teardown/cleanup


def table_structure_queries(conn):
    """Retrieves the table structures from the given database connection"""
    with conn.cursor() as cursor:
        cursor.execute("SHOW TABLES;")
        tables = tuple(row[0] for row in cursor.fetchall())
        queries = []
        for table in tables:
            cursor.execute(f"SHOW CREATE TABLE {table}")
            query = cursor.fetchone()
            queries.append(re.sub(
                r" AUTO_INCREMENT=[0-9]* ", r" AUTO_INCREMENT=0 ",
                query[1]))

    return queries

@pytest.fixture(scope="session")
def db_conn():
    """Create a db connection fixture for tests"""
    # 01) Generate random string to append to all test db artifacts for the session
    rand_str = random_string(15)
    live_db_details = parse_db_url(SQL_URI)
    test_db_host = os.environ.get("TEST_DB_HOST", live_db_details[0])
    test_db_port = int(os.environ.get("TEST_DB_PORT", live_db_details[4]))
    test_db_user = os.environ.get("TEST_DB_USER", live_db_details[1])
    test_db_passwd = os.environ.get("TEST_DB_PASSWD", live_db_details[2])
    test_db_name = f"test_{live_db_details[3]}_{rand_str}"
    test_sql_uri_prefix = (
        f"mysql://{test_db_user}:{test_db_passwd}@{test_db_host}"
        f"{':' + str(test_db_port) if test_db_port else ''}")
    #
    # 02) Create new test db
    #     * Connect to the test db host
    #     * Use context manager to ensure the connection is automatically closed
    #       on exit
    with database_connector(test_sql_uri_prefix) as prefix_db_conn:
        with prefix_db_conn.cursor() as db_cursor:
            db_cursor.execute(f"CREATE DATABASE {test_db_name}")
            #
            # 03) Copy over table structure from source db
            with database_connector() as src_db_conn:
                queries = table_structure_queries(src_db_conn)
            #
            # 04) get database connection to test db and yield it up
            test_db_conn = database_connector(
                f"{test_sql_uri_prefix}/{test_db_name}")
            with test_db_conn.cursor() as temp_cur:
                # dump copied structure to test db
                for query in queries:
                    temp_cur.execute(query)

            yield test_db_conn
            #
            # 05) Clean up after ourselves
            #   a.) Close the test db connection
            test_db_conn.close()
            #
            #   b.) Delete the test database
            db_cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
