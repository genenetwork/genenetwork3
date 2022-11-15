"""Test functions dealing with group management."""
from uuid import UUID

import pytest

from gn3.auth import db
from gn3.auth.authorisation.groups import Group, create_group

create_group_failure = {
    "status": "error",
    "message": "Unauthorised: Failed to create group."
}

group_leader_id = lambda : UUID("d32611e3-07fc-4564-b56c-786c6db6de2b")

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user_id,expected", (
    ("ecb52977-3004-469e-9428-2a1856725c7f", Group(
        UUID("d32611e3-07fc-4564-b56c-786c6db6de2b"), "a_test_group")),
    ("21351b66-8aad-475b-84ac-53ce528451e3", create_group_failure),
    ("ae9c6245-0966-41a5-9a5e-20885a96bea7", create_group_failure),
    ("9a0c7ce5-2f40-4e78-979e-bf3527a59579", create_group_failure),
    ("e614247d-84d2-491d-a048-f80b578216cb", create_group_failure)))
def test_create_group(# pylint: disable=[too-many-arguments]
        test_app, auth_testdb_path, mocker, test_users, user_id, expected):# pylint: disable=[unused-argument]
    """
    GIVEN: an authenticated user
    WHEN: the user attempts to create a group
    THEN: verify they are only able to create the group if they have the
          appropriate privileges
    """
    mocker.patch("gn3.auth.authorisation.groups.uuid4", group_leader_id)
    with test_app.app_context() as flask_context:
        flask_context.g.user_id = UUID(user_id)
        with db.connection(auth_testdb_path) as conn:
            assert create_group(conn, "a_test_group") == expected
