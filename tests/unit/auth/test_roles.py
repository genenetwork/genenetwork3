"""Test functions dealing with group management."""
import uuid

import pytest

from gn3.auth import db
from gn3.auth.authorisation.privileges import Privilege
from gn3.auth.authorisation.roles import Role, create_role

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
    "user_id,expected", (
    ("ecb52977-3004-469e-9428-2a1856725c7f", Role(
        uuid.UUID("d32611e3-07fc-4564-b56c-786c6db6de2b"), "a_test_role",
        PRIVILEGES)),
    ("21351b66-8aad-475b-84ac-53ce528451e3", create_role_failure),
    ("ae9c6245-0966-41a5-9a5e-20885a96bea7", create_role_failure),
    ("9a0c7ce5-2f40-4e78-979e-bf3527a59579", create_role_failure),
    ("e614247d-84d2-491d-a048-f80b578216cb", create_role_failure)))
def test_create_role(# pylint: disable=[too-many-arguments]
        test_app, auth_testdb_path, mocker, test_users, user_id, expected):# pylint: disable=[unused-argument]
    """
    GIVEN: an authenticated user
    WHEN: the user attempts to create a role
    THEN: verify they are only able to create the role if they have the
          appropriate privileges
    """
    mocker.patch("gn3.auth.authorisation.roles.uuid4", uuid_fn)
    with test_app.app_context() as flask_context:
        flask_context.g.user_id = uuid.UUID(user_id)
        with db.connection(auth_testdb_path) as conn, db.cursor(conn) as cursor:
            the_role = create_role(cursor, "a_test_role", PRIVILEGES)
            assert the_role == expected
