"""Test the privileges module"""
import pytest

from gn3.auth import db
from gn3.auth.authorisation.privileges import Privilege, user_privileges

from tests.unit.auth import conftest

SORT_KEY = lambda x: x.privilege_id

PRIVILEGES = sorted(
    (Privilege("system:group:create-group", "Create a group"),
     Privilege("system:group:view-group", "View the details of a group"),
     Privilege("system:group:edit-group", "Edit the details of a group"),
     Privilege("system:user:list", "List users in the system"),
     Privilege("system:group:delete-group", "Delete a group"),
     Privilege("group:user:add-group-member", "Add a user to a group"),
     Privilege("group:user:remove-group-member", "Remove a user from a group"),
     Privilege("system:group:transfer-group-leader",
               "Transfer leadership of the group to some other member"),

     Privilege("group:resource:create-resource", "Create a resource object"),
     Privilege("group:resource:view-resource",
               "view a resource and use it in computations"),
     Privilege("group:resource:edit-resource", "edit/update a resource"),
     Privilege("group:resource:delete-resource", "Delete a resource"),

     Privilege("group:role:create-role", "Create a new role"),
     Privilege("group:role:edit-role", "edit/update an existing role"),
     Privilege("group:user:assign-role", "Assign a role to an existing user"),
     Privilege("group:role:delete-role", "Delete an existing role")),
    key=SORT_KEY)

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user,expected", tuple(zip(
        conftest.TEST_USERS, (PRIVILEGES, [], [], [], []))))
def test_user_privileges(auth_testdb_path, fxtr_users, user, expected):# pylint: disable=[unused-argument]
    """
    GIVEN: A user
    WHEN: An attempt is made to fetch the user's privileges
    THEN: Ensure only
    """
    with db.connection(auth_testdb_path) as conn:
        assert sorted(
            user_privileges(conn, user), key=SORT_KEY) == expected
