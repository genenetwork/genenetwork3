"""Fixtures and utilities for user-related tests"""
import uuid

import pytest

from gn3.auth import db
from gn3.auth.authentication.users import User

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
