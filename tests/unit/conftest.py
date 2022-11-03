"""Fixtures for unit tests."""
from typing import Union
from pathlib import Path
from datetime import datetime
from tempfile import TemporaryDirectory

import pytest
from yoyo import get_backend
from yoyo.migrations import Migration, MigrationList

from gn3.app import create_app
from gn3.migrations import apply_migrations, rollback_migrations

@pytest.fixture(scope="session")
def client():
    """Create a test client fixture for tests"""
    # Do some setup
    with TemporaryDirectory() as testdir:
        testdb = Path(testdir).joinpath(
            f'testdb_{datetime.now().strftime("%Y%m%dT%H%M%S")}')
        app = create_app({"AUTH_DB": testdb})
        app.config.update({"TESTING": True})
        app.testing = True
        yield app.test_client()
        # Clean up after ourselves
        testdb.unlink(missing_ok=True)

@pytest.fixture()
def test_app_config(client): # pylint: disable=redefined-outer-name
    """Return the test application's configuration object"""
    return client.application.config

@pytest.fixture()
def auth_testdb(test_app_config): # pylint: disable=redefined-outer-name
    """Get the test application's auth database file"""
    return test_app_config["AUTH_DB"]

def apply_single_migration(db_uri: Union[Path, str], migration: Migration):
    """Utility to apply a single migration"""
    apply_migrations(get_backend(f"sqlite:///{db_uri}"), MigrationList([migration]))

def rollback_single_migration(db_uri: Union[Path, str], migration: Migration):
    """Utility to rollback a single migration"""
    rollback_migrations(get_backend(f"sqlite:///{db_uri}"), MigrationList([migration]))
