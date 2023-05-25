"""Handle the management of resource/user groups."""
import json
from uuid import UUID, uuid4
from functools import reduce
from typing import Any, Sequence, Iterable, Optional, NamedTuple

from flask import g
from pymonad.maybe import Just, Maybe, Nothing

from gn3.auth import db
from gn3.auth.dictify import dictify
from gn3.auth.authentication.users import User, user_by_id

from ..checks import authorised_p
from ..privileges import Privilege
from ..errors import NotFoundError, AuthorisationError, InconsistencyError
from ..roles.models import (
    Role, create_role, check_user_editable, revoke_user_role_by_name,
    assign_user_role_by_name)

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

DUMMY_GROUP = Group(
    group_id=UUID("77cee65b-fe29-4383-ae41-3cb3b480cc70"),
    group_name="GN3_DUMMY_GROUP",
    group_metadata={
        "group-description": "This is a dummy group to use as a placeholder"
    })

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
        error_description = (
            f"User '{user.name} ({user.email})' is a member of {len(groups)} "
            f"groups ({groups_str})")
        super().__init__(f"{type(self).__name__}: {error_description}.")

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

@authorised_p(
    privileges = ("system:group:create-group",),
    error_description = (
        "You do not have the appropriate privileges to enable you to "
        "create a new group."),
    oauth2_scope = "profile group")
def create_group(
        conn: db.DbConnection, group_name: str, group_leader: User,
        group_description: Optional[str] = None) -> Group:
    """Create a new group."""
    user_groups = user_membership(conn, group_leader)
    if len(user_groups) > 0:
        raise MembershipError(group_leader, user_groups)

    with db.cursor(conn) as cursor:
        new_group = save_group(
            cursor, group_name,(
                {"group_description": group_description}
                if group_description else {}))
        add_user_to_group(cursor, new_group, group_leader)
        revoke_user_role_by_name(cursor, group_leader, "group-creator")
        assign_user_role_by_name(cursor, group_leader, "group-leader")
        return new_group

@authorised_p(("group:role:create-role",),
              error_description="Could not create the group role")
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

def user_group(conn: db.DbConnection, user: User) -> Maybe[Group]:
    """Returns the given user's group"""
    with db.cursor(conn) as cursor:
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

def is_group_leader(conn: db.DbConnection, user: User, group: Group) -> bool:
    """Check whether the given `user` is the leader of `group`."""

    ugroup = user_group(conn, user).maybe(
        False, lambda val: val) # type: ignore[arg-type, misc]
    if not group:
        # User cannot be a group leader if not a member of ANY group
        return False

    if not ugroup == group:
        # User cannot be a group leader if not a member of THIS group
        return False

    with db.cursor(conn) as cursor:
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

def save_group(
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

@authorised_p(
    privileges = ("system:group:view-group",),
    error_description = (
        "You do not have the appropriate privileges to access the list of users"
        " in the group."))
def group_users(conn: db.DbConnection, group_id: UUID) -> Iterable[User]:
    """Retrieve all users that are members of group with id `group_id`."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "SELECT u.* FROM group_users AS gu INNER JOIN users AS u "
            "ON gu.user_id = u.user_id WHERE gu.group_id=:group_id",
            {"group_id": str(group_id)})
        results = cursor.fetchall()

    return (User(UUID(row["user_id"]), row["email"], row["name"])
            for row in results)

@authorised_p(
    privileges = ("system:group:view-group",),
    error_description = (
        "You do not have the appropriate privileges to access the group."))
def group_by_id(conn: db.DbConnection, group_id: UUID) -> Group:
    """Retrieve a group by its ID"""
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM groups WHERE group_id=:group_id",
                       {"group_id": str(group_id)})
        row = cursor.fetchone()
        if row:
            return Group(
                UUID(row["group_id"]),
                row["group_name"],
                json.loads(row["group_metadata"]))

    raise NotFoundError(f"Could not find group with ID '{group_id}'.")

@authorised_p(("system:group:view-group", "system:group:edit-group"),
              error_description=("You do not have the appropriate authorisation"
                                 " to act upon the join requests."),
              oauth2_scope="profile group")
def join_requests(conn: db.DbConnection, user: User):
    """List all the join requests for the user's group."""
    with db.cursor(conn) as cursor:
        group = user_group(conn, user).maybe(DUMMY_GROUP, lambda grp: grp)# type: ignore[misc]
        if group != DUMMY_GROUP and is_group_leader(conn, user, group):
            cursor.execute(
                "SELECT gjr.*, u.email, u.name FROM group_join_requests AS gjr "
                "INNER JOIN users AS u ON gjr.requester_id=u.user_id "
                "WHERE gjr.group_id=? AND gjr.status='PENDING'",
                (str(group.group_id),))
            return tuple(dict(row)for row in cursor.fetchall())

    raise AuthorisationError(
        "You do not have the appropriate authorisation to access the "
        "group's join requests.")

@authorised_p(("system:group:view-group", "system:group:edit-group"),
              error_description=("You do not have the appropriate authorisation"
                                 " to act upon the join requests."),
              oauth2_scope="profile group")
def accept_reject_join_request(
        conn: db.DbConnection, request_id: UUID, user: User, status: str) -> dict:
    """Accept/Reject a join request."""
    assert status in ("ACCEPTED", "REJECTED"), f"Invalid status '{status}'."
    with db.cursor(conn) as cursor:
        group = user_group(conn, user).maybe(DUMMY_GROUP, lambda grp: grp) # type: ignore[misc]
        cursor.execute("SELECT * FROM group_join_requests WHERE request_id=?",
                       (str(request_id),))
        row = cursor.fetchone()
        if row:
            if group.group_id == UUID(row["group_id"]):
                try:
                    the_user = user_by_id(conn, UUID(row["requester_id"]))
                    if status == "ACCEPTED":
                        add_user_to_group(cursor, group, the_user)
                        revoke_user_role_by_name(cursor, the_user, "group-creator")
                    cursor.execute(
                        "UPDATE group_join_requests SET status=? "
                        "WHERE request_id=?",
                        (status, str(request_id)))
                    return {"request_id": request_id, "status": status}
                except NotFoundError as nfe:
                    raise InconsistencyError(
                        "Could not find user associated with join request."
                    ) from nfe
            raise AuthorisationError(
                "You cannot act on other groups join requests")
        raise NotFoundError(f"Could not find request with ID '{request_id}'")

def __organise_privileges__(acc, row):
    role_id = UUID(row["role_id"])
    role = acc.get(role_id, False)
    if role:
        return {
            **acc,
            role_id: Role(
                role.role_id, role.role_name,
                bool(int(row["user_editable"])),
                role.privileges + (
                    Privilege(row["privilege_id"],
                              row["privilege_description"]),))
        }
    return {
        **acc,
        role_id: Role(
            UUID(row["role_id"]), row["role_name"],
            bool(int(row["user_editable"])),
            (Privilege(row["privilege_id"], row["privilege_description"]),))
    }

# @authorised_p(("group:role:view",),
#               "Insufficient privileges to view role",
#               oauth2_scope="profile group role")
def group_role_by_id(
        conn: db.DbConnection, group: Group, group_role_id: UUID) -> GroupRole:
    """Retrieve GroupRole from id by its `group_role_id`."""
    ## TODO: do privileges check before running actual query
    ##       the check commented out above doesn't work correctly
    with db.cursor(conn) as cursor:
        cursor.execute(
            "SELECT gr.group_role_id, r.*, p.* "
            "FROM group_roles AS gr "
            "INNER JOIN roles AS r ON gr.role_id=r.role_id "
            "INNER JOIN role_privileges AS rp ON rp.role_id=r.role_id "
            "INNER JOIN privileges AS p ON p.privilege_id=rp.privilege_id "
            "WHERE gr.group_role_id=? AND gr.group_id=?",
            (str(group_role_id), str(group.group_id)))
        rows = cursor.fetchall()
        if rows:
            roles: tuple[Role,...] = tuple(reduce(
                __organise_privileges__, rows, {}).values())
            assert len(roles) == 1
            return GroupRole(group_role_id, group, roles[0])
        raise NotFoundError(
            f"Group role with ID '{group_role_id}' does not exist.")

@authorised_p(("group:role:edit-role",),
              "You do not have the privilege to edit a role.",
              oauth2_scope="profile group role")
def add_privilege_to_group_role(conn: db.DbConnection, group_role: GroupRole,
                                privilege: Privilege) -> GroupRole:
    """Add `privilege` to `group_role`."""
    ## TODO: do privileges check.
    check_user_editable(group_role.role)
    with db.cursor(conn) as cursor:
        cursor.execute(
            "INSERT INTO role_privileges(role_id,privilege_id) "
            "VALUES (?, ?) ON CONFLICT (role_id, privilege_id) "
            "DO NOTHING",
            (str(group_role.role.role_id), str(privilege.privilege_id)))
        return GroupRole(
            group_role.group_role_id,
            group_role.group,
            Role(group_role.role.role_id,
                 group_role.role.role_name,
                 group_role.role.user_editable,
                 group_role.role.privileges + (privilege,)))

@authorised_p(("group:role:edit-role",),
              "You do not have the privilege to edit a role.",
              oauth2_scope="profile group role")
def delete_privilege_from_group_role(
        conn: db.DbConnection, group_role: GroupRole,
        privilege: Privilege) -> GroupRole:
    """Delete `privilege` to `group_role`."""
    ## TODO: do privileges check.
    check_user_editable(group_role.role)
    with db.cursor(conn) as cursor:
        cursor.execute(
            "DELETE FROM role_privileges WHERE "
            "role_id=? AND privilege_id=?",
            (str(group_role.role.role_id), str(privilege.privilege_id)))
        return GroupRole(
            group_role.group_role_id,
            group_role.group,
            Role(group_role.role.role_id,
                 group_role.role.role_name,
                 group_role.role.user_editable,
                 tuple(priv for priv in group_role.role.privileges
                       if priv != privilege)))
