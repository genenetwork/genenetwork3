"""Fixtures and utilities for migration-related tests"""
import pytest
from yoyo.backends import DatabaseBackend
from yoyo import get_backend, read_migrations
from yoyo.migrations import Migration, MigrationList

from gn3.auth import db
from gn3.migrations import apply_migrations, rollback_migrations

@pytest.fixture(scope="session")
def auth_testdb_path(fxtr_app_config): # pylint: disable=redefined-outer-name
    """Get the test application's auth database file"""
    return fxtr_app_config["AUTH_DB"]

@pytest.fixture(scope="session")
def auth_migrations_dir(fxtr_app_config): # pylint: disable=redefined-outer-name
    """Get the test application's auth database file"""
    return fxtr_app_config["AUTH_MIGRATIONS"]

def apply_single_migration(backend: DatabaseBackend, migration: Migration):# pylint: disable=[redefined-outer-name]
    """Utility to apply a single migration"""
    apply_migrations(backend, MigrationList([migration]))

def rollback_single_migration(backend: DatabaseBackend, migration: Migration):# pylint: disable=[redefined-outer-name]
    """Utility to rollback a single migration"""
    rollback_migrations(backend, MigrationList([migration]))

@pytest.fixture(scope="session")
def backend(auth_testdb_path):# pylint: disable=redefined-outer-name
    """Fixture: retrieve yoyo backend for auth database"""
    return get_backend(f"sqlite:///{auth_testdb_path}")

@pytest.fixture(scope="session")
def all_migrations(auth_migrations_dir): # pylint: disable=redefined-outer-name
    """Retrieve all the migrations"""
    return read_migrations(auth_migrations_dir)

@pytest.fixture(scope="function")
def conn_after_auth_migrations(backend, auth_testdb_path, all_migrations): # pylint: disable=redefined-outer-name
    """Run all migrations and return a connection to the database after"""
    apply_migrations(backend, all_migrations)
    with db.connection(auth_testdb_path) as conn:
        yield conn

    rollback_migrations(backend, all_migrations)

def migrations_up_to(migration, migrations_dir):
    """Run all the migration before `migration`."""
    migrations = read_migrations(migrations_dir)
    index = [mig.path for mig in migrations].index(migration)
    return MigrationList(migrations[0:index])
