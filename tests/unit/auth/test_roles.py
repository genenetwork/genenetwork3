"""Test functions dealing with group management."""
import uuid

import pytest

from gn3.auth import db
from gn3.auth.authorisation.privileges import Privilege
from gn3.auth.authorisation.errors import AuthorisationError
from gn3.auth.authorisation.roles.models import Role, user_roles, create_role

from tests.unit.auth import conftest
from tests.unit.auth.fixtures import TEST_USERS

create_role_failure = {
    "status": "error",
    "message": "Unauthorised: Could not create role"
}

uuid_fn = lambda : uuid.UUID("d32611e3-07fc-4564-b56c-786c6db6de2b")

PRIVILEGES = (
    Privilege("group:resource:view-resource",
              "view a resource and use it in computations"),
    Privilege("group:resource:edit-resource", "edit/update a resource"))

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user,expected", tuple(zip(conftest.TEST_USERS[0:1], (
        Role(uuid.UUID("d32611e3-07fc-4564-b56c-786c6db6de2b"), "a_test_role",
             True, PRIVILEGES),))))
def test_create_role(# pylint: disable=[too-many-arguments]
        fxtr_app, auth_testdb_path, mocker, fxtr_users, user, expected):# pylint: disable=[unused-argument]
    """
    GIVEN: an authenticated user
    WHEN: the user attempts to create a role
    THEN: verify they are only able to create the role if they have the
          appropriate privileges
    """
    mocker.patch("gn3.auth.authorisation.roles.models.uuid4", uuid_fn)
    mocker.patch("gn3.auth.authorisation.checks.require_oauth.acquire",
                 conftest.get_tokeniser(user))
    with db.connection(auth_testdb_path) as conn, db.cursor(conn) as cursor:
        the_role = create_role(cursor, "a_test_role", PRIVILEGES)
        assert the_role == expected

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user,expected", tuple(zip(conftest.TEST_USERS[1:], (
        create_role_failure, create_role_failure, create_role_failure))))
def test_create_role_raises_exception_for_unauthorised_users(# pylint: disable=[too-many-arguments]
        fxtr_app, auth_testdb_path, mocker, fxtr_users, user, expected):# pylint: disable=[unused-argument]
    """
    GIVEN: an authenticated user
    WHEN: the user attempts to create a role
    THEN: verify they are only able to create the role if they have the
          appropriate privileges
    """
    mocker.patch("gn3.auth.authorisation.roles.models.uuid4", uuid_fn)
    mocker.patch("gn3.auth.authorisation.checks.require_oauth.acquire",
                 conftest.get_tokeniser(user))
    with db.connection(auth_testdb_path) as conn, db.cursor(conn) as cursor:
        with pytest.raises(AuthorisationError):
            create_role(cursor, "a_test_role", PRIVILEGES)

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user,expected",
    (zip(TEST_USERS,
         ((Role(
             role_id=uuid.UUID('a0e67630-d502-4b9f-b23f-6805d0f30e30'),
             role_name='group-leader', user_editable=False,
             privileges=(
                 Privilege(privilege_id='group:resource:create-resource',
                           privilege_description='Create a resource object'),
                 Privilege(privilege_id='group:resource:delete-resource',
                           privilege_description='Delete a resource'),
                 Privilege(privilege_id='group:resource:edit-resource',
                           privilege_description='edit/update a resource'),
                 Privilege(
                     privilege_id='group:resource:view-resource',
                     privilege_description=(
                         'view a resource and use it in computations')),
                 Privilege(privilege_id='group:role:create-role',
                           privilege_description='Create a new role'),
                 Privilege(privilege_id='group:role:delete-role',
                           privilege_description='Delete an existing role'),
                 Privilege(privilege_id='group:role:edit-role',
                           privilege_description='edit/update an existing role'),
                 Privilege(privilege_id='group:user:add-group-member',
                           privilege_description='Add a user to a group'),
                 Privilege(privilege_id='group:user:assign-role',
                           privilege_description=(
                               'Assign a role to an existing user')),
                 Privilege(privilege_id='group:user:remove-group-member',
                           privilege_description='Remove a user from a group'),
                 Privilege(privilege_id='system:group:delete-group',
                           privilege_description='Delete a group'),
                 Privilege(privilege_id='system:group:edit-group',
                           privilege_description='Edit the details of a group'),
                 Privilege(
                     privilege_id='system:group:transfer-group-leader',
                     privilege_description=(
                         'Transfer leadership of the group to some other '
                         'member')),
                 Privilege(privilege_id='system:group:view-group',
                           privilege_description='View the details of a group'),
                 Privilege(privilege_id='system:user:list',
                           privilege_description='List users in the system'))),
           Role(
               role_id=uuid.UUID("ade7e6b0-ba9c-4b51-87d0-2af7fe39a347"),
               role_name="group-creator", user_editable=False,
               privileges=(
                   Privilege(privilege_id='system:group:create-group',
                             privilege_description = "Create a group"),))),
          tuple(), tuple(), tuple()))))
def test_user_roles(fxtr_group_user_roles, user, expected):
    """
    GIVEN: an authenticated user
    WHEN: we request the user's privileges
    THEN: return **ALL** the privileges attached to the user
    """
    conn, *_others = fxtr_group_user_roles
    assert user_roles(conn, user) == expected
