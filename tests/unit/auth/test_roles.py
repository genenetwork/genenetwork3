"""Test functions dealing with group management."""
import uuid

import pytest

from gn3.auth import db
from gn3.auth.authorisation.privileges import Privilege
from gn3.auth.authorisation.roles import Role, user_roles, create_role

from tests.unit.auth import conftest
from tests.unit.auth.fixtures import TEST_USERS

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

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user,expected",
    (zip(TEST_USERS,
         ((Role(
             role_id=uuid.UUID('a0e67630-d502-4b9f-b23f-6805d0f30e30'),
             role_name='group-leader',
             privileges=(
                 Privilege(
                     privilege_id=uuid.UUID('13ec2a94-4f1a-442d-aad2-936ad6dd5c57'),
                     privilege_name='delete-group'),
                 Privilege(
                     privilege_id=uuid.UUID('1c59eff5-9336-4ed2-a166-8f70d4cb012e'),
                     privilege_name='delete-role'),
                 Privilege(
                     privilege_id=uuid.UUID('221660b1-df05-4be1-b639-f010269dbda9'),
                     privilege_name='create-role'),
                 Privilege(
                     privilege_id=uuid.UUID('2f980855-959b-4339-b80e-25d1ec286e21'),
                     privilege_name='edit-resource'),
                 Privilege(
                     privilege_id=uuid.UUID('3ebfe79c-d159-4629-8b38-772cf4bc2261'),
                     privilege_name='view-group'),
                 Privilege(
                     privilege_id=uuid.UUID('4842e2aa-38b9-4349-805e-0a99a9cf8bff'),
                     privilege_name='create-group'),
                 Privilege(
                     privilege_id=uuid.UUID('5103cc68-96f8-4ebb-83a4-a31692402c9b'),
                     privilege_name='assign-role'),
                 Privilege(
                     privilege_id=uuid.UUID('52576370-b3c7-4e6a-9f7e-90e9dbe24d8f'),
                     privilege_name='edit-group'),
                 Privilege(
                     privilege_id=uuid.UUID('7bcca363-cba9-4169-9e31-26bdc6179b28'),
                     privilege_name='edit-role'),
                 Privilege(
                     privilege_id=uuid.UUID('7f261757-3211-4f28-a43f-a09b800b164d'),
                     privilege_name='view-resource'),
                 Privilege(
                     privilege_id=uuid.UUID('aa25b32a-bff2-418d-b0a2-e26b4a8f089b'),
                     privilege_name='create-resource'),
                 Privilege(
                     privilege_id=uuid.UUID('ae4add8c-789a-4d11-a6e9-a306470d83d9'),
                     privilege_name='add-group-member'),
                 Privilege(
                     privilege_id=uuid.UUID('d2a070fd-e031-42fb-ba41-d60cf19e5d6d'),
                     privilege_name='delete-resource'),
                 Privilege(
                     privilege_id=uuid.UUID('d4afe2b3-4ca0-4edd-b37d-966535b5e5bd'),
                     privilege_name='transfer-group-leadership'),
             Privilege(
                 privilege_id=uuid.UUID('f1bd3f42-567e-4965-9643-6d1a52ddee64'),
                 privilege_name='remove-group-member'))),),
          tuple(), tuple(), tuple()))))
def test_user_roles(fxtr_group_user_roles, user, expected):
    """
    GIVEN: an authenticated user
    WHEN: we request the user's privileges
    THEN: return **ALL** the privileges attached to the user
    """
    assert user_roles(fxtr_group_user_roles, user) == expected
