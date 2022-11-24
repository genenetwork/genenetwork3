"""Test the privileges module"""
from uuid import UUID

import pytest

from gn3.auth import db
from gn3.auth.authorisation.privileges import Privilege, user_privileges

from tests.unit.auth import conftest

SORT_KEY = lambda x: x.privilege_name

PRIVILEGES = sorted(
    (Privilege(UUID("4842e2aa-38b9-4349-805e-0a99a9cf8bff"), "create-group"),
     Privilege(UUID("3ebfe79c-d159-4629-8b38-772cf4bc2261"), "view-group"),
     Privilege(UUID("52576370-b3c7-4e6a-9f7e-90e9dbe24d8f"), "edit-group"),
     Privilege(UUID("13ec2a94-4f1a-442d-aad2-936ad6dd5c57"), "delete-group"),
     Privilege(UUID("ae4add8c-789a-4d11-a6e9-a306470d83d9"),
               "add-group-member"),
     Privilege(UUID("f1bd3f42-567e-4965-9643-6d1a52ddee64"),
               "remove-group-member"),
     Privilege(UUID("d4afe2b3-4ca0-4edd-b37d-966535b5e5bd"),
               "transfer-group-leadership"),

     Privilege(UUID("aa25b32a-bff2-418d-b0a2-e26b4a8f089b"), "create-resource"),
     Privilege(UUID("7f261757-3211-4f28-a43f-a09b800b164d"), "view-resource"),
     Privilege(UUID("2f980855-959b-4339-b80e-25d1ec286e21"), "edit-resource"),
     Privilege(UUID("d2a070fd-e031-42fb-ba41-d60cf19e5d6d"), "delete-resource"),

     Privilege(UUID("221660b1-df05-4be1-b639-f010269dbda9"), "create-role"),
     Privilege(UUID("7bcca363-cba9-4169-9e31-26bdc6179b28"), "edit-role"),
     Privilege(UUID("5103cc68-96f8-4ebb-83a4-a31692402c9b"), "assign-role"),
     Privilege(UUID("1c59eff5-9336-4ed2-a166-8f70d4cb012e"), "delete-role")),
    key=SORT_KEY)

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user,expected", tuple(zip(
        conftest.TEST_USERS, (PRIVILEGES, [], [], [], []))))
def test_user_privileges(auth_testdb_path, test_users, user, expected):# pylint: disable=[unused-argument]
    """
    GIVEN: A user
    WHEN: An attempt is made to fetch the user's privileges
    THEN: Ensure only
    """
    with db.connection(auth_testdb_path) as conn:
        assert sorted(
            user_privileges(conn, user), key=SORT_KEY) == expected
