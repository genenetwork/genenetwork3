"""Fixtures and utilities for role-related tests"""
import uuid

import pytest

from gn3.auth import db
from gn3.auth.authorisation.roles import Role
from gn3.auth.authorisation.privileges import Privilege

RESOURCE_READER_ROLE = Role(
    uuid.UUID("c3ca2507-ee24-4835-9b31-8c21e1c072d3"), "resource_reader", True,
    (Privilege("group:resource:view-resource",
               "view a resource and use it in computations"),))

RESOURCE_EDITOR_ROLE = Role(
    uuid.UUID("89819f84-6346-488b-8955-86062e9eedb7"), "resource_editor", True,
    (
        Privilege("group:resource:view-resource",
                  "view a resource and use it in computations"),
        Privilege("group:resource:edit-resource", "edit/update a resource")))

TEST_ROLES = (RESOURCE_READER_ROLE, RESOURCE_EDITOR_ROLE)

@pytest.fixture(scope="function")
def fxtr_roles(conn_after_auth_migrations):
    """Setup some example roles."""
    with db.cursor(conn_after_auth_migrations) as cursor:
        cursor.executemany(
            ("INSERT INTO roles VALUES (?, ?, ?)"),
            ((str(role.role_id), role.role_name, 1) for role in TEST_ROLES))
        cursor.executemany(
            ("INSERT INTO role_privileges VALUES (?, ?)"),
            ((str(role.role_id), str(privilege.privilege_id))
             for role in TEST_ROLES for privilege in role.privileges))

    yield conn_after_auth_migrations, TEST_ROLES

    with db.cursor(conn_after_auth_migrations) as cursor:
        cursor.executemany(
            ("DELETE FROM role_privileges WHERE role_id=? AND privilege_id=?"),
            ((str(role.role_id), str(privilege.privilege_id))
             for role in TEST_ROLES for privilege in role.privileges))
        cursor.executemany(
            ("DELETE FROM roles WHERE role_id=?"),
            ((str(role.role_id),) for role in TEST_ROLES))
