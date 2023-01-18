"""Test resource-management functions"""
import uuid

import pytest

from gn3.auth import db
from gn3.auth.authorisation.groups import Group
from gn3.auth.authorisation.resources import (
    Resource, user_resources, create_resource, ResourceCategory,
    public_resources)

from tests.unit.auth import conftest

group = Group(uuid.UUID("9988c21d-f02f-4d45-8966-22c968ac2fbf"), "TheTestGroup")
resource_category = ResourceCategory(
    uuid.UUID("fad071a3-2fc8-40b8-992b-cdefe7dcac79"), "mrna", "mRNA Dataset")
create_resource_failure = {
    "status": "error",
    "message": "Unauthorised: Could not create resource"
}
uuid_fn = lambda : uuid.UUID("d32611e3-07fc-4564-b56c-786c6db6de2b")

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user,expected",
    tuple(zip(
        conftest.TEST_USERS,
        (Resource(
            group, uuid.UUID("d32611e3-07fc-4564-b56c-786c6db6de2b"),
            "test_resource", resource_category, False),
         create_resource_failure,
         create_resource_failure,
         create_resource_failure,
         create_resource_failure))))
def test_create_resource(mocker, fxtr_app, fxtr_users_in_group, user, expected):
    """Test that resource creation works as expected."""
    mocker.patch("gn3.auth.authorisation.resources.uuid4", uuid_fn)
    conn, _group, _users = fxtr_users_in_group
    with fxtr_app.app_context() as flask_context, db.cursor(conn) as cursor:
        flask_context.g.user = user
        assert create_resource(conn, "test_resource", resource_category) == expected

        # Cleanup
        cursor.execute(
            "DELETE FROM resources WHERE resource_id=?", (str(uuid_fn()),))

SORTKEY = lambda resource: resource.resource_id

@pytest.mark.unit_test
def test_public_resources(fxtr_resources):
    """
    GIVEN: some resources in the database
    WHEN: public resources are requested
    THEN: only list the resources that are public
    """
    conn, _res = fxtr_resources
    assert sorted(public_resources(conn), key=SORTKEY) == sorted(tuple(
        res for res in conftest.TEST_RESOURCES if res.public), key=SORTKEY)

PUBLIC_RESOURCES = sorted(conftest.TEST_RESOURCES_PUBLIC, key=SORTKEY)

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "user,expected",
    tuple(zip(
        conftest.TEST_USERS,
        (sorted(
            set(conftest.TEST_RESOURCES_GROUP_01).union(
                conftest.TEST_RESOURCES_PUBLIC),
            key=SORTKEY),
         sorted(
             set([conftest.TEST_RESOURCES_GROUP_01[1]]).union(
                 conftest.TEST_RESOURCES_PUBLIC),
             key=SORTKEY),
         PUBLIC_RESOURCES, PUBLIC_RESOURCES))))
def test_user_resources(fxtr_group_user_roles, user, expected):
    """
    GIVEN: some resources in the database
    WHEN: a particular user's resources are requested
    THEN: list only the resources for which the user can access
    """
    conn, *_others = fxtr_group_user_roles
    assert sorted(user_resources(conn, user), key=SORTKEY) == expected
