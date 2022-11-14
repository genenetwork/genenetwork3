"""Fixtures for auth tests."""
import sqlite3
from pathlib import Path
from typing import Union
from contextlib import closing

import pytest
from yoyo.backends import DatabaseBackend
from yoyo import get_backend, read_migrations
from yoyo.migrations import Migration, MigrationList

from gn3.migrations import apply_migrations, rollback_migrations

@pytest.fixture(scope="session")
def auth_testdb_path(test_app_config): # pylint: disable=redefined-outer-name
    """Get the test application's auth database file"""
    return test_app_config["AUTH_DB"]

@pytest.fixture(scope="session")
def auth_migrations_dir(test_app_config): # pylint: disable=redefined-outer-name
    """Get the test application's auth database file"""
    return test_app_config["AUTH_MIGRATIONS"]

def apply_single_migration(backend: DatabaseBackend, migration: Migration):
    """Utility to apply a single migration"""
    apply_migrations(backend, MigrationList([migration]))

def rollback_single_migration(backend: DatabaseBackend, migration: Migration):
    """Utility to rollback a single migration"""
    rollback_migrations(backend, MigrationList([migration]))

@pytest.fixture(scope="session")
def backend(auth_testdb_path): # pylint: disable=redefined-outer-name
    return get_backend(f"sqlite:///{auth_testdb_path}")

@pytest.fixture(scope="session")
def all_migrations(auth_migrations_dir): # pylint: disable=redefined-outer-name
    return read_migrations(auth_migrations_dir)

@pytest.fixture(scope="function")
def conn_after_auth_migrations(backend, auth_testdb_path, all_migrations): # pylint: disable=redefined-outer-name
    """Run all migrations and return a connection to the database after"""
    apply_migrations(backend, all_migrations)
    with closing(sqlite3.connect(auth_testdb_path)) as conn:
        yield conn

    rollback_migrations(backend, all_migrations)

def migrations_up_to(migration, migrations_dir):
    migrations = read_migrations(migrations_dir)
    index = [mig.path for mig in migrations].index(migration)
    return MigrationList(migrations[0:index])

@pytest.fixture(scope="function")
def test_users(conn_after_auth_migrations):
    query = "INSERT INTO users(user_id, email, name) VALUES (?, ?, ?)"
    query_user_roles = "INSERT INTO user_roles(user_id, role_id) VALUES (?, ?)"
    test_users = (
        ("ecb52977-3004-469e-9428-2a1856725c7f", "group@lead.er",
         "Group Leader"),
        ("21351b66-8aad-475b-84ac-53ce528451e3", "group@mem.ber01",
         "Group Member 01"),
        ("ae9c6245-0966-41a5-9a5e-20885a96bea7", "group@mem.ber02",
         "Group Member 02"),
        ("9a0c7ce5-2f40-4e78-979e-bf3527a59579", "unaff@iliated.user",
         "Unaffiliated User"))
    test_user_roles = (
        ("ecb52977-3004-469e-9428-2a1856725c7f",
         "a0e67630-d502-4b9f-b23f-6805d0f30e30"),)
    with closing(conn_after_auth_migrations.cursor()) as cursor:
        cursor.executemany(query, test_users)
        cursor.executemany(query_user_roles, test_user_roles)
        conn_after_auth_migrations.commit()

    yield conn_after_auth_migrations

    with closing(conn_after_auth_migrations.cursor()) as cursor:
        cursor.executemany(
            "DELETE FROM user_roles WHERE user_id=?",
            (("ecb52977-3004-469e-9428-2a1856725c7f",),))
        cursor.executemany(
            "DELETE FROM users WHERE user_id=?",
            (("ecb52977-3004-469e-9428-2a1856725c7f",),
             ("21351b66-8aad-475b-84ac-53ce528451e3",),
             ("ae9c6245-0966-41a5-9a5e-20885a96bea7",),
             ("9a0c7ce5-2f40-4e78-979e-bf3527a59579",)))
        conn_after_auth_migrations.commit()
