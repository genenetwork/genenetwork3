"""Module that holds fixtures for integration tests"""
import pytest

from gn3.app import create_app
from gn3.db_utils import database_connector

@pytest.fixture(scope="session")
def client():
    """Create a test client fixture for tests"""
    # Do some setup
    app = create_app()
    app.config.update({"TESTING": True})
    app.testing = True
    yield app.test_client()
    # Do some teardown/cleanup


@pytest.fixture
def db_conn():
    """Create a db connection fixture for tests"""
    ## Update this to use temp db once that is in place
    conn = database_connector()
    yield conn
    conn.close()
