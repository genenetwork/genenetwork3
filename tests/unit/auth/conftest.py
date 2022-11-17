"""Fixtures for auth tests."""
import uuid

import pytest
from yoyo.backends import DatabaseBackend
from yoyo import get_backend, read_migrations
from yoyo.migrations import Migration, MigrationList

from gn3.auth import db
from gn3.auth.authentication.users import User
from gn3.auth.authorisation.groups import Group
from gn3.migrations import apply_migrations, rollback_migrations

@pytest.fixture(scope="session")
def auth_testdb_path(test_app_config): # pylint: disable=redefined-outer-name
    """Get the test application's auth database file"""
    return test_app_config["AUTH_DB"]

@pytest.fixture(scope="session")
def auth_migrations_dir(test_app_config): # pylint: disable=redefined-outer-name
    """Get the test application's auth database file"""
    return test_app_config["AUTH_MIGRATIONS"]

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

@pytest.fixture(scope="function")
def test_group(conn_after_auth_migrations):# pylint: disable=[redefined-outer-name]
    """Fixture: setup a test group."""
    query = "INSERT INTO groups(group_id, group_name) VALUES (?, ?)"
    group_id = uuid.UUID("9988c21d-f02f-4d45-8966-22c968ac2fbf")
    group_name = "TheTestGroup"
    with db.cursor(conn_after_auth_migrations) as cursor:
        cursor.execute(query, (str(group_id), group_name))

    yield (conn_after_auth_migrations, Group(group_id, group_name))

@pytest.fixture(scope="function")
def test_users(conn_after_auth_migrations):# pylint: disable=[redefined-outer-name]
    """Fixture: setup test users."""
    query = "INSERT INTO users(user_id, email, name) VALUES (?, ?, ?)"
    query_user_roles = "INSERT INTO user_roles(user_id, role_id) VALUES (?, ?)"
    the_users = (
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
    with db.cursor(conn_after_auth_migrations) as cursor:
        cursor.executemany(query, the_users)
        cursor.executemany(query_user_roles, test_user_roles)

    yield (conn_after_auth_migrations, tuple(
        User(uuid.UUID(uid), email, name) for uid, email, name in the_users))

    with db.cursor(conn_after_auth_migrations) as cursor:
        cursor.executemany(
            "DELETE FROM user_roles WHERE user_id=?",
            (("ecb52977-3004-469e-9428-2a1856725c7f",),))
        cursor.executemany(
            "DELETE FROM users WHERE user_id=?",
            (("ecb52977-3004-469e-9428-2a1856725c7f",),
             ("21351b66-8aad-475b-84ac-53ce528451e3",),
             ("ae9c6245-0966-41a5-9a5e-20885a96bea7",),
             ("9a0c7ce5-2f40-4e78-979e-bf3527a59579",)))

@pytest.fixture(scope="function")
def test_users_in_group(test_group, test_users):#pytest: disable=[redefined-outer-name]
    """Link the users to the groups."""
    conn = test_group[0]
    group = test_group[1]
    users = test_users[1]
    query_params = (
        (str(group.group_id), str(user.user_id)) for user in users
        if user.email not in ("unaff@iliated.user",))
    with db.cursor(conn) as cursor:
        cursor.execute(
            "INSERT INTO group_users(group_id, user_id) VALUES (?, ?)",
            query_params)

    yield (conn, group, users)

    with db.cursor(conn) as cursor:
        cursor.execute(
            "DELETE FROM group_users WHERE group_id=? AND user_id=?",
            query_params)
