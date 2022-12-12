"""Fixtures and utilities for group-related tests"""
import uuid

import pytest

from gn3.auth import db
from gn3.auth.authorisation.groups import Group

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
