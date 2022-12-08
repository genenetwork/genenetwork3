"""Fixtures for auth tests."""
import uuid

import pytest
from yoyo.backends import DatabaseBackend
from yoyo import get_backend, read_migrations
from yoyo.migrations import Migration, MigrationList

from gn3.auth import db
from gn3.auth.authentication.users import User
from gn3.auth.authorisation.groups import Group
from gn3.auth.authorisation.resources import Resource, ResourceCategory

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

TEST_GROUPS = (
    Group(uuid.UUID("9988c21d-f02f-4d45-8966-22c968ac2fbf"), "TheTestGroup"),
    Group(uuid.UUID("e37d59d7-c05e-4d67-b479-81e627d8d634"), "TheTestGroup"))

@pytest.fixture(scope="function")
def test_group(conn_after_auth_migrations):# pylint: disable=[redefined-outer-name]
    """Fixture: setup a test group."""
    query = "INSERT INTO groups(group_id, group_name) VALUES (?, ?)"
    with db.cursor(conn_after_auth_migrations) as cursor:
        cursor.executemany(
            query, tuple(
                (str(group.group_id), group.group_name)
                for group in TEST_GROUPS))

    yield (conn_after_auth_migrations, TEST_GROUPS[0])

TEST_USERS = (
        User(uuid.UUID("ecb52977-3004-469e-9428-2a1856725c7f"), "group@lead.er",
             "Group Leader"),
        User(uuid.UUID("21351b66-8aad-475b-84ac-53ce528451e3"),
             "group@mem.ber01", "Group Member 01"),
        User(uuid.UUID("ae9c6245-0966-41a5-9a5e-20885a96bea7"),
             "group@mem.ber02", "Group Member 02"),
        User(uuid.UUID("9a0c7ce5-2f40-4e78-979e-bf3527a59579"),
             "unaff@iliated.user", "Unaffiliated User"))

@pytest.fixture(scope="function")
def test_users(conn_after_auth_migrations):# pylint: disable=[redefined-outer-name]
    """Fixture: setup test users."""
    query = "INSERT INTO users(user_id, email, name) VALUES (?, ?, ?)"
    query_user_roles = "INSERT INTO user_roles(user_id, role_id) VALUES (?, ?)"
    test_user_roles = (
        ("ecb52977-3004-469e-9428-2a1856725c7f",
         "a0e67630-d502-4b9f-b23f-6805d0f30e30"),)
    with db.cursor(conn_after_auth_migrations) as cursor:
        cursor.executemany(query, (
            (str(user.user_id), user.email, user.name) for user in TEST_USERS))
        cursor.executemany(query_user_roles, test_user_roles)

    yield (conn_after_auth_migrations, TEST_USERS)

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
def test_users_in_group(test_group, test_users):# pylint: disable=[redefined-outer-name]
    """Link the users to the groups."""
    conn = test_group[0]
    group = test_group[1]
    users = test_users[1]
    query_params = tuple(
        (str(group.group_id), str(user.user_id)) for user in users
        if user.email not in ("unaff@iliated.user",))
    with db.cursor(conn) as cursor:
        cursor.executemany(
            "INSERT INTO group_users(group_id, user_id) VALUES (?, ?)",
            query_params)

    yield (conn, group, users)

    with db.cursor(conn) as cursor:
        cursor.executemany(
            "DELETE FROM group_users WHERE group_id=? AND user_id=?",
            query_params)

TEST_RESOURCES = (
    Resource(TEST_GROUPS[0], uuid.UUID("26ad1668-29f5-439d-b905-84d551f85955"),
             "ResourceG01R01",
             ResourceCategory(uuid.UUID("48056f84-a2a6-41ac-8319-0e1e212cba2a"),
                              "genotype", "Genotype Dataset"),
             True),
    Resource(TEST_GROUPS[0], uuid.UUID("2130aec0-fefd-434d-92fd-9ca342348b2d"),
             "ResourceG01R02",
             ResourceCategory(uuid.UUID("548d684b-d4d1-46fb-a6d3-51a56b7da1b3"),
                              "phenotype", "Phenotype (Publish) Dataset"),
             False),
    Resource(TEST_GROUPS[0], uuid.UUID("e9a1184a-e8b4-49fb-b713-8d9cbeea5b83"),
             "ResourceG01R03",
             ResourceCategory(uuid.UUID("fad071a3-2fc8-40b8-992b-cdefe7dcac79"),
                              "mrna", "mRNA Dataset"),
             False),
    Resource(TEST_GROUPS[1], uuid.UUID("14496a1c-c234-49a2-978c-8859ea274054"),
             "ResourceG02R01",
             ResourceCategory(uuid.UUID("48056f84-a2a6-41ac-8319-0e1e212cba2a"),
                              "genotype", "Genotype Dataset"),
             False),
    Resource(TEST_GROUPS[1], uuid.UUID("04ad9e09-94ea-4390-8a02-11f92999806b"),
             "ResourceG02R02",
             ResourceCategory(uuid.UUID("fad071a3-2fc8-40b8-992b-cdefe7dcac79"),
                              "mrna", "mRNA Dataset"),
             True))

@pytest.fixture(scope="function")
def test_resources(test_group):# pylint: disable=[redefined-outer-name]
    """fixture: setup test resources in the database"""
    conn, _group = test_group
    with db.cursor(conn) as cursor:
        cursor.executemany(
            "INSERT INTO resources VALUES (?,?,?,?,?)",
        ((str(res.group.group_id), str(res.resource_id), res.resource_name,
          str(res.resource_category.resource_category_id),
          1 if res.public else 0) for res in TEST_RESOURCES))
    return (conn, TEST_RESOURCES)

@pytest.fixture(scope="function")
def fixture_user_resources(test_users_in_group, test_resources):# pylint: disable=[redefined-outer-name, unused-argument]
    """fixture: link users to roles and resources"""
    conn, _resources = test_resources
    ## TODO: setup user roles
    ## TODO: attach user roles to specific resources
    return conn
