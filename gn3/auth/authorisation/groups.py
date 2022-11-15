"""Handle the management of resource/user groups."""
from uuid import UUID, uuid4
from typing import Iterable, NamedTuple

from gn3.auth import db
from .privileges import Privilege
from .roles import Role, create_role
from .checks import authorised_p

class Group(NamedTuple):
    """Class representing a group."""
    group_id: UUID
    group_name: str

@authorised_p(("create-group",), error_message="Failed to create group.")
def create_group(conn: db.DbConnection, group_name: str) -> Group:
    """Create a group"""
    group = Group(uuid4(), group_name)
    with db.cursor(conn) as cursor:
        ## Maybe check whether the user is already a member of a group
        ## if they are not a member of any group, proceed to create the group
        ## if they are a member of a group, then fail with an exception
        cursor.execute(
            "INSERT INTO groups(group_id, group_name) VALUES (?, ?)",
            (str(group.group_id), group_name))
        ## Maybe assign `group-leader` role to user creating the group

    return group

@authorised_p(("create-role",), error_message="Could not create the group role")
def create_group_role(
        conn: db.DbConnection, group: Group, role_name: str,
        privileges: Iterable[Privilege]) -> Role:
    """Create a role attached to a group."""
    with db.cursor(conn) as cursor:
        role = create_role(cursor, role_name, privileges)
        cursor.execute(
            "INSERT INTO group_roles(group_id, role_id) VALUES(?, ?)",
            (str(group.group_id), role.role_id))

    return role
