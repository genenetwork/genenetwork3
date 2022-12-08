"""Handle the management of resources."""
from uuid import UUID, uuid4
from typing import Sequence, NamedTuple

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
    public: bool

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

def resource_categories(conn: db.DbConnection) -> Sequence[ResourceCategory]:
    """Retrieve all available resource categories"""
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM resource_categories")
        return tuple(
            ResourceCategory(UUID(row[0]), row[1], row[2])
            for row in cursor.fetchall())
    return tuple()

def public_resources(conn: db.DbConnection) -> Sequence[Resource]:
    """List all resources marked as public"""
    categories = {
        str(cat.resource_category_id): cat for cat in resource_categories(conn)
    }
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM resources WHERE public=1")
        results = cursor.fetchall()
        group_uuids = tuple(row[0] for row in results)
        query = ("SELECT * FROM groups WHERE group_id IN "
                 f"({', '.join(['?'] * len(group_uuids))})")
        cursor.execute(query, group_uuids)
        groups = {row[0]: Group(UUID(row[0]), row[1]) for row in cursor.fetchall()}
        return tuple(
            Resource(groups[row[0]], UUID(row[1]), row[2], categories[row[3]],
                     bool(row[4]))
            for row in results)
