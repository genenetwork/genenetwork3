"""Fixtures for unit tests."""
from pathlib import Path
from datetime import datetime
from tempfile import TemporaryDirectory

import pytest

from gn3.app import create_app

@pytest.fixture(scope="session")
def test_app():
    # Do some setup
    with TemporaryDirectory() as testdir:
        testdb = Path(testdir).joinpath(
            f'testdb_{datetime.now().strftime("%Y%m%dT%H%M%S")}')
        app = create_app()
        app.config.update({"TESTING": True, "AUTH_DB": testdb})
        app.testing = True
        yield app
        # Clean up after ourselves
        testdb.unlink(missing_ok=True)

@pytest.fixture(scope="session")
def client(test_app):
    """Create a test client fixture for tests"""
    with test_app.app_context():
        yield test_app.test_client()

@pytest.fixture(scope="session")
def test_app_config(client): # pylint: disable=redefined-outer-name
    """Return the test application's configuration object"""
    return client.application.config
