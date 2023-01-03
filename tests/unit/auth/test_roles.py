"""Test functions dealing with group management."""
import uuid

import pytest

from gn3.auth import db
from gn3.auth.authorisation.privileges import Privilege
from gn3.auth.authorisation.roles import Role, create_role

from tests.unit.auth import conftest

create_role_failure = {
    "status": "error",
    "message": "Unauthorised: Could not create role"
}

uuid_fn = lambda : uuid.UUID("d32611e3-07fc-4564-b56c-786c6db6de2b")

PRIVILEGES = (
    Privilege(uuid.UUID("7f261757-3211-4f28-a43f-a09b800b164d"),
              "view-resource"),
    Privilege(uuid.UUID("2f980855-959b-4339-b80e-25d1ec286e21"),
              "edit-resource"))

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user,expected", tuple(zip(conftest.TEST_USERS, (
        Role(
            uuid.UUID("d32611e3-07fc-4564-b56c-786c6db6de2b"), "a_test_role",
            PRIVILEGES), create_role_failure, create_role_failure,
        create_role_failure, create_role_failure))))
def test_create_role(# pylint: disable=[too-many-arguments]
        fxtr_app, auth_testdb_path, mocker, fxtr_users, user, expected):# pylint: disable=[unused-argument]
    """
    GIVEN: an authenticated user
    WHEN: the user attempts to create a role
    THEN: verify they are only able to create the role if they have the
          appropriate privileges
    """
    mocker.patch("gn3.auth.authorisation.roles.uuid4", uuid_fn)
    with fxtr_app.app_context() as flask_context:
        flask_context.g.user = user
        with db.connection(auth_testdb_path) as conn, db.cursor(conn) as cursor:
            the_role = create_role(cursor, "a_test_role", PRIVILEGES)
            assert the_role == expected
