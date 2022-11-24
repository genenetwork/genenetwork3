"""Test resource-management functions"""
import uuid

import pytest

from gn3.auth.authorisation.groups import Group
from gn3.auth.authorisation.resources import (
    Resource, create_resource, ResourceCategory)

group = Group(uuid.UUID("9988c21d-f02f-4d45-8966-22c968ac2fbf"), "TheTestGroup")
resource_category = ResourceCategory(
    uuid.UUID("fad071a3-2fc8-40b8-992b-cdefe7dcac79"), "mrna", "mRNA Dataset")
create_resource_failure = {
    "status": "error",
    "message": "Unauthorised: Could not create resource"
}

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user_id,expected", (
    ("ecb52977-3004-469e-9428-2a1856725c7f", Resource(
        group, uuid.UUID("d32611e3-07fc-4564-b56c-786c6db6de2b"),
        "test_resource", resource_category)),
    ("21351b66-8aad-475b-84ac-53ce528451e3", create_resource_failure),
    ("ae9c6245-0966-41a5-9a5e-20885a96bea7", create_resource_failure),
    ("9a0c7ce5-2f40-4e78-979e-bf3527a59579", create_resource_failure),
    ("e614247d-84d2-491d-a048-f80b578216cb", create_resource_failure)))
def test_create_resource(test_app, test_users_in_group, user_id, expected):
    """Test that resource creation works as expected."""
    conn, _group, _users = test_users_in_group
    with test_app.app_context() as flask_context:
        flask_context.g.user_id = uuid.UUID(user_id)
        assert create_resource(conn, "test_resource", resource_category) == expected
