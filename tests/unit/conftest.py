"""Fixtures for unit tests."""
from pathlib import Path
from datetime import datetime
from tempfile import TemporaryDirectory

import pytest

from gn3.app import create_app

@pytest.fixture(scope="session")
def fxtr_app():
    """Fixture: setup the test app"""
    # Do some setup
    with TemporaryDirectory() as testdir:
        testdb = Path(testdir).joinpath(
            f'testdb_{datetime.now().strftime("%Y%m%dT%H%M%S")}')
        app = create_app({
            "TESTING": True, "AUTH_DB": testdb,
            "OAUTH2_ACCESS_TOKEN_GENERATOR": "tests.unit.auth.test_token.gen_token"
        })
        app.testing = True
        yield app
        # Clean up after ourselves
        testdb.unlink(missing_ok=True)

@pytest.fixture(scope="session")
def client(fxtr_app): # pylint: disable=redefined-outer-name
    """Create a test client fixture for tests"""
    with fxtr_app.app_context():
        yield fxtr_app.test_client()

@pytest.fixture(scope="session")
def fxtr_app_config(client): # pylint: disable=redefined-outer-name
    """Return the test application's configuration object"""
    return client.application.config
