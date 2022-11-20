"""Handle the management of resource/user groups."""
from uuid import UUID, uuid4
from typing import Sequence, Iterable, NamedTuple

from gn3.auth import db
from gn3.auth.authentication.users import User

from .privileges import Privilege
from .roles import Role, create_role
from .checks import authorised_p

class Group(NamedTuple):
    """Class representing a group."""
    group_id: UUID
    group_name: str

class GroupRole(NamedTuple):
    """Class representing a role tied/belonging to a group."""
    group_role_id: UUID
    role: Role

class MembershipError(Exception):
    """Raised when there is an error with a user's membership to a group."""

    def __init__(self, user: User, groups: Sequence[Group]):
        """Initialise the `MembershipError` exception object."""
        groups_str = ", ".join(group.group_name for group in groups)
        error_message = (
            f"User '{user.name} ({user.email})' is a member of {len(groups)} "
            f"groups ({groups_str})")
        super().__init__(f"{type(self).__name__}: {error_message}.")

def user_membership(conn: db.DbConnection, user: User) -> Sequence[Group]:
    """Returns all the groups that a member belongs to"""
    query = (
        "SELECT groups.group_id, group_name FROM group_users INNER JOIN groups "
        "ON group_users.group_id=groups.group_id "
        "WHERE group_users.user_id=?")
    with db.cursor(conn) as cursor:
        cursor.execute(query, (str(user.user_id),))
        groups = tuple(Group(row[0], row[1]) for row in cursor.fetchall())

    return groups

@authorised_p(("create-group",), error_message="Failed to create group.")
def create_group(conn: db.DbConnection, group_name: str,
                 group_leader: User) -> Group:
    """Create a group"""
    group = Group(uuid4(), group_name)
    user_groups = user_membership(conn, group_leader)
    if len(user_groups) > 0:
        raise MembershipError(group_leader, user_groups)

    with db.cursor(conn) as cursor:
        cursor.execute(
            "INSERT INTO groups(group_id, group_name) VALUES (?, ?)",
            (str(group.group_id), group_name))
        cursor.execute(
            "INSERT INTO group_users VALUES (?, ?)",
            (str(group.group_id), str(group_leader.user_id)))

    return group

@authorised_p(("create-role",), error_message="Could not create the group role")
def create_group_role(
        conn: db.DbConnection, group: Group, role_name: str,
        privileges: Iterable[Privilege]) -> GroupRole:
    """Create a role attached to a group."""
    with db.cursor(conn) as cursor:
        group_role_id = uuid4()
        role = create_role(cursor, role_name, privileges)
        cursor.execute(
            ("INSERT INTO group_roles(group_role_id, group_id, role_id) "
             "VALUES(?, ?, ?)"),
            (str(group_role_id), str(group.group_id), str(role.role_id)))

    return GroupRole(group_role_id, role)
