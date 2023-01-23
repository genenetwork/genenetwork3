"""Handle the management of resources."""
import json
from uuid import UUID, uuid4
from typing import Dict, Sequence, NamedTuple

from gn3.auth import db
from gn3.auth.authentication.users import User

from .checks import authorised_p
from .errors import AuthorisationError
from .groups import Group, user_group, is_group_leader, authenticated_user_group

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

@authorised_p(("group:resource:create-resource",),
              error_message="Could not create resource")
def create_resource(
        conn: db.DbConnection, resource_name: str,
        resource_category: ResourceCategory) -> Resource:
    """Create a resource item."""
    with db.cursor(conn) as cursor:
        group = authenticated_user_group(conn).maybe(False, lambda val: val)
        if not group:
            raise MissingGroupError(
                "User with no group cannot create a resource.")
        resource = Resource(group, uuid4(), resource_name, resource_category, False)
        cursor.execute(
            "INSERT INTO resources VALUES (?, ?, ?, ?, ?)",
            (str(resource.group.group_id), str(resource.resource_id),
             resource_name,
             str(resource.resource_category.resource_category_id),
             1 if resource.public else 0))

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
        groups = {
            row[0]: Group(
                UUID(row[0]), row[1], json.loads(row[2] or "{}"))
            for row in cursor.fetchall()
        }
        return tuple(
            Resource(groups[row[0]], UUID(row[1]), row[2], categories[row[3]],
                     bool(row[4]))
            for row in results)

def group_leader_resources(
        cursor: db.DbCursor, user: User, group: Group,
        res_categories: Dict[UUID, ResourceCategory]) -> Sequence[Resource]:
    """Return all the resources available to the group leader"""
    if is_group_leader(cursor, user, group):
        cursor.execute("SELECT * FROM resources WHERE group_id=?",
                       (str(group.group_id),))
        return tuple(
            Resource(group, UUID(row[1]), row[2], res_categories[UUID(row[3])],
                     bool(row[4]))
            for row in cursor.fetchall())
    return tuple()

def user_resources(conn: db.DbConnection, user: User) -> Sequence[Resource]:
    """List the resources available to the user"""
    categories = { # Repeated in `public_resources` function
        cat.resource_category_id: cat for cat in resource_categories(conn)
    }
    with db.cursor(conn) as cursor:
        def __all_resources__(group) -> Sequence[Resource]:
            gl_resources = group_leader_resources(cursor, user, group, categories)

            cursor.execute(
                ("SELECT resources.* FROM group_user_roles_on_resources "
                 "LEFT JOIN resources "
                 "ON group_user_roles_on_resources.resource_id=resources.resource_id "
                 "WHERE group_user_roles_on_resources.group_id = ? "
                 "AND group_user_roles_on_resources.user_id = ?"),
                (str(group.group_id), str(user.user_id)))
            private_res = tuple(
                Resource(group, UUID(row[1]), row[2], categories[UUID(row[3])],
                         bool(row[4]))
                for row in cursor.fetchall())
            return tuple({
                res.resource_id: res
                for res in
                (private_res + gl_resources + public_resources(conn))# type: ignore[operator]
            }.values())

        # Fix the typing here
        return user_group(cursor, user).map(__all_resources__).maybe(# type: ignore[arg-type,misc]
            public_resources(conn), lambda res: res)# type: ignore[arg-type,return-value]
