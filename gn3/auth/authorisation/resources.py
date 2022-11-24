"""Handle the management of resources."""
from uuid import UUID, uuid4
from typing import NamedTuple

from gn3.auth import db
from .checks import authorised_p
from .exceptions import AuthorisationError
from .groups import Group, authenticated_user_group

class MissingGroupError(AuthorisationError):
    """Raised for any resource operation without a group."""

class ResourceCategory(NamedTuple):
    """Class representing a resource category."""
    resource_category_id: UUID
    resource_category_key: str
    resource_category_description: str

class Resource(NamedTuple):
    """Class representing a resource."""
    group: Group
    resource_id: UUID
    resource_name: str
    resource_category: ResourceCategory

@authorised_p(("create-resource",),  error_message="Could not create resource")
def create_resource(
        conn: db.DbConnection, resource_name: str,
        resource_category: ResourceCategory) -> Resource:
    """Create a resource item."""
    with db.cursor(conn) as cursor:
        group = authenticated_user_group(conn).maybe(False, lambda val: val)
        if not group:
            raise MissingGroupError(
                "User with no group cannot create a resource.")
        resource = Resource(group, uuid4(), resource_name, resource_category)
        cursor.execute(
            ("INSERT INTO resources VALUES (?, ?, ?, ?)"),
            (str(resource.group.group_id), str(resource.resource_id),
             resource_name,
             str(resource.resource_category.resource_category_id)))

    return resource
