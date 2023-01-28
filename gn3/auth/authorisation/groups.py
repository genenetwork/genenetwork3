"""Handle the management of resource/user groups."""
import json
from uuid import UUID, uuid4
from typing import Any, Sequence, Iterable, Optional, NamedTuple

from flask import g
from pymonad.maybe import Just, Maybe, Nothing

from gn3.auth import db
from gn3.auth.dictify import dictify
from gn3.auth.authentication.users import User
from gn3.auth.authentication.checks import authenticated_p

from .checks import authorised_p
from .privileges import Privilege
from .errors import AuthorisationError
from .roles import (
    Role, create_role, revoke_user_role_by_name, assign_user_role_by_name)

class Group(NamedTuple):
    """Class representing a group."""
    group_id: UUID
    group_name: str
    group_metadata: dict[str, Any]

    def dictify(self):
        """Return a dict representation of `Group` objects."""
        return {
            "group_id": self.group_id, "group_name": self.group_name,
            "group_metadata": self.group_metadata
        }

class GroupRole(NamedTuple):
    """Class representing a role tied/belonging to a group."""
    group_role_id: UUID
    group: Group
    role: Role

    def dictify(self) -> dict[str, Any]:
        """Return a dict representation of `GroupRole` objects."""
        return {
            "group_role_id": self.group_role_id, "group": dictify(self.group),
            "role": dictify(self.role)
        }

class GroupCreationError(AuthorisationError):
    """Raised whenever a group creation fails"""

class MembershipError(AuthorisationError):
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
        "SELECT groups.group_id, group_name, groups.group_metadata "
        "FROM group_users INNER JOIN groups "
        "ON group_users.group_id=groups.group_id "
        "WHERE group_users.user_id=?")
    with db.cursor(conn) as cursor:
        cursor.execute(query, (str(user.user_id),))
        groups = tuple(Group(row[0], row[1], json.loads(row[2]))
                       for row in cursor.fetchall())

    return groups

@authenticated_p
def create_group(
        conn: db.DbConnection, group_name: str, group_leader: User,
        group_description: Optional[str] = None) -> Group:
    """Create a new group."""
    user_groups = user_membership(conn, group_leader)
    if len(user_groups) > 0:
        raise MembershipError(group_leader, user_groups)

    @authorised_p(
        ("system:group:create-group",), (
            "You do not have the appropriate privileges to enable you to "
            "create a new group."),
        group_leader)
    def __create_group__():
        with db.cursor(conn) as cursor:
            new_group = __save_group__(
                cursor, group_name,(
                    {"group_description": group_description}
                    if group_description else {}))
            add_user_to_group(cursor, new_group, group_leader)
            revoke_user_role_by_name(cursor, group_leader, "group-creator")
            assign_user_role_by_name(cursor, group_leader, "group-leader")
            return new_group

    return __create_group__()

@authenticated_p
@authorised_p(("group:role:create-role",),
              error_message="Could not create the group role")
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

    return GroupRole(group_role_id, group, role)

@authenticated_p
def authenticated_user_group(conn) -> Maybe:
    """
    Returns the currently authenticated user's group.

    Look into returning a Maybe object.
    """
    user = g.user
    with db.cursor(conn) as cursor:
        cursor.execute(
            ("SELECT groups.* FROM group_users "
             "INNER JOIN groups ON group_users.group_id=groups.group_id "
             "WHERE group_users.user_id = ?"),
            (str(user.user_id),))
        groups = tuple(Group(UUID(row[0]), row[1], json.loads(row[2] or "{}"))
                       for row in cursor.fetchall())

    if len(groups) > 1:
        raise MembershipError(user, groups)

    if len(groups) == 1:
        return Just(groups[0])

    return Nothing

def user_group(cursor: db.DbCursor, user: User) -> Maybe[Group]:
    """Returns the given user's group"""
    cursor.execute(
        ("SELECT groups.group_id, groups.group_name, groups.group_metadata "
         "FROM group_users "
         "INNER JOIN groups ON group_users.group_id=groups.group_id "
         "WHERE group_users.user_id = ?"),
        (str(user.user_id),))
    groups = tuple(
        Group(UUID(row[0]), row[1], json.loads(row[2] or "{}"))
        for row in cursor.fetchall())

    if len(groups) > 1:
        raise MembershipError(user, groups)

    if len(groups) == 1:
        return Just(groups[0])

    return Nothing

def is_group_leader(cursor: db.DbCursor, user: User, group: Group):
    """Check whether the given `user` is the leader of `group`."""
    ugroup = user_group(cursor, user).maybe(False, lambda val: val) # type: ignore[arg-type, misc]
    if not group:
        # User cannot be a group leader if not a member of ANY group
        return False

    if not ugroup == group:
        # User cannot be a group leader if not a member of THIS group
        return False

    cursor.execute(
        ("SELECT roles.role_name FROM user_roles LEFT JOIN roles "
         "ON user_roles.role_id = roles.role_id WHERE user_id = ?"),
        (str(user.user_id),))
    role_names = tuple(row[0] for row in cursor.fetchall())

    return "group-leader" in role_names

def all_groups(conn: db.DbConnection) -> Maybe[Sequence[Group]]:
    """Retrieve all existing groups"""
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM groups")
        res = cursor.fetchall()
        if res:
            return Just(tuple(
                Group(row["group_id"], row["group_name"],
                      json.loads(row["group_metadata"])) for row in res))

    return Nothing

def __save_group__(
        cursor: db.DbCursor, group_name: str,
        group_metadata: dict[str, Any]) -> Group:
    """Save a group to db"""
    the_group = Group(uuid4(), group_name, group_metadata)
    cursor.execute(
        ("INSERT INTO groups "
         "VALUES(:group_id, :group_name, :group_metadata) "
         "ON CONFLICT (group_id) DO UPDATE SET "
         "group_name=:group_name, group_metadata=:group_metadata"),
    {"group_id": str(the_group.group_id), "group_name": the_group.group_name,
     "group_metadata": json.dumps(the_group.group_metadata)})
    return the_group

def add_user_to_group(cursor: db.DbCursor, the_group: Group, user: User):
    """Add `user` to `the_group` as a member."""
    cursor.execute(
        ("INSERT INTO group_users VALUES (:group_id, :user_id) "
         "ON CONFLICT (group_id, user_id) DO NOTHING"),
        {"group_id": str(the_group.group_id), "user_id": str(user.user_id)})
