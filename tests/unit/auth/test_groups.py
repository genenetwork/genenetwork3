"""Test functions dealing with group management."""
from uuid import UUID

import pytest
from pymonad.maybe import Nothing

from gn3.auth import db
from gn3.auth.authentication.users import User
from gn3.auth.authorisation.roles import Role
from gn3.auth.authorisation.privileges import Privilege
from gn3.auth.authorisation.groups import (
    Group, GroupRole, user_group, create_group, MembershipError, create_group_role)

from tests.unit.auth import conftest

create_group_failure = {
    "status": "error",
    "message": "Unauthorised: Failed to create group."
}

uuid_fn = lambda : UUID("d32611e3-07fc-4564-b56c-786c6db6de2b")

GROUP = Group(UUID("9988c21d-f02f-4d45-8966-22c968ac2fbf"), "TheTestGroup")
PRIVILEGES = (
    Privilege(
        UUID("7f261757-3211-4f28-a43f-a09b800b164d"), "view-resource"),
    Privilege(
        UUID("2f980855-959b-4339-b80e-25d1ec286e21"), "edit-resource"))

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user,expected", tuple(zip(conftest.TEST_USERS, (
        Group(
            UUID("d32611e3-07fc-4564-b56c-786c6db6de2b"), "a_test_group"),
        create_group_failure, create_group_failure, create_group_failure,
        create_group_failure))))
def test_create_group(# pylint: disable=[too-many-arguments]
        test_app, auth_testdb_path, mocker, test_users, user, expected):# pylint: disable=[unused-argument]
    """
    GIVEN: an authenticated user
    WHEN: the user attempts to create a group
    THEN: verify they are only able to create the group if they have the
          appropriate privileges
    """
    mocker.patch("gn3.auth.authorisation.groups.uuid4", uuid_fn)
    with test_app.app_context() as flask_context:
        flask_context.g.user = user
        with db.connection(auth_testdb_path) as conn:
            assert create_group(conn, "a_test_group", user) == expected

create_role_failure = {
    "status": "error",
    "message": "Unauthorised: Could not create the group role"
}

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user,expected", tuple(zip(conftest.TEST_USERS, (
        GroupRole(
            UUID("d32611e3-07fc-4564-b56c-786c6db6de2b"),
            GROUP,
            Role(UUID("d32611e3-07fc-4564-b56c-786c6db6de2b"),
                 "ResourceEditor", PRIVILEGES)),
        create_role_failure, create_role_failure, create_role_failure,
        create_role_failure))))
def test_create_group_role(mocker, test_users_in_group, test_app, user, expected):
    """
    GIVEN: an authenticated user
    WHEN: the user attempts to create a role, attached to a group
    THEN: verify they are only able to create the role if they have the
        appropriate privileges and that the role is attached to the given group
    """
    mocker.patch("gn3.auth.authorisation.groups.uuid4", uuid_fn)
    mocker.patch("gn3.auth.authorisation.roles.uuid4", uuid_fn)
    conn, _group, _users = test_users_in_group
    with test_app.app_context() as flask_context:
        flask_context.g.user = user
        assert create_group_role(
            conn, GROUP, "ResourceEditor", PRIVILEGES) == expected

@pytest.mark.unit_test
def test_create_multiple_groups(mocker, test_app, test_users):
    """
    GIVEN: An authenticated user with appropriate authorisation
    WHEN: The user attempts to create a new group, while being a member of an
      existing group
    THEN: The system should prevent that, and respond with an appropriate error
      message
    """
    mocker.patch("gn3.auth.authorisation.groups.uuid4", uuid_fn)
    user = User(
        UUID("ecb52977-3004-469e-9428-2a1856725c7f"), "group@lead.er",
        "Group Leader")
    conn, _test_users = test_users
    with test_app.app_context() as flask_context:
        flask_context.g.user = user
        # First time, successfully creates the group
        assert create_group(conn, "a_test_group", user) == Group(
            UUID("d32611e3-07fc-4564-b56c-786c6db6de2b"), "a_test_group")
        # subsequent attempts should fail
        with pytest.raises(MembershipError):
            create_group(conn, "another_test_group", user)

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user,expected",
    tuple(zip(
        conftest.TEST_USERS,
        (([Group(UUID("9988c21d-f02f-4d45-8966-22c968ac2fbf"), "TheTestGroup")] * 3)
         + [Nothing]))))
def test_user_group(test_users_in_group, user, expected):
    """
    GIVEN: A bunch of registered users, some of whom are members of a group, and
      others are not
    WHEN: a particular user's group is requested,
    THEN: return a Maybe containing the group that the user belongs to, or
      Nothing
    """
    conn, _group, _users = test_users_in_group
    with db.cursor(conn) as cursor:
        assert (
            user_group(cursor, user).maybe(Nothing, lambda val: val)
            == expected)
