"""Handle the management of resource/user groups."""
from uuid import UUID, uuid4
from typing import Iterable, NamedTuple

from gn3.auth import db
from .privileges import Privilege
from .roles import Role, create_role
from .checks import authorised_p

@authorised_p(
    ("create-group",), success_message="Successfully created group.",
    error_message="Failed to create group.")
def create_group(conn, group_name):
class Group(NamedTuple):
    """Class representing a group."""
    group_id: UUID
    group_name: str

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
