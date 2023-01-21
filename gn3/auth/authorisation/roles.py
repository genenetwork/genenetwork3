"""Handle management of roles"""
from uuid import UUID, uuid4
from functools import reduce
from typing import Sequence, Iterable, NamedTuple

from pymonad.maybe import Just, Maybe, Nothing

from gn3.auth import db
from gn3.auth.authentication.users import User
from gn3.auth.authentication.checks import authenticated_p

from .checks import authorised_p
from .privileges import Privilege

class Role(NamedTuple):
    """Class representing a role: creates immutable objects."""
    role_id: UUID
    role_name: str
    privileges: Iterable[Privilege]

@authenticated_p
@authorised_p(("group:role:create-role",), error_message="Could not create role")
def create_role(
        cursor: db.DbCursor, role_name: str,
        privileges: Iterable[Privilege]) -> Role:
    """
    Create a new generic role.

    PARAMS:
    * cursor: A database cursor object - This function could be used as part of
              a transaction, hence the use of a cursor rather than a connection
              object.
    * role_name: The name of the role
    * privileges: A 'list' of privileges to assign the new role

    RETURNS: An immutable `gn3.auth.authorisation.roles.Role` object
    """
    role = Role(uuid4(), role_name, privileges)

    cursor.execute(
        "INSERT INTO roles(role_id, role_name) VALUES (?, ?)",
        (str(role.role_id), role.role_name))
    cursor.executemany(
        "INSERT INTO role_privileges(role_id, privilege_id) VALUES (?, ?)",
        tuple((str(role.role_id), str(priv.privilege_id))
              for priv in privileges))

    return role

def __organise_privileges__(roles_dict, privilege_row):
    """Organise the privileges into their roles."""
    role_id_str = privilege_row["role_id"]
    if  role_id_str in roles_dict:
        return {
            **roles_dict,
            role_id_str: Role(
                UUID(role_id_str),
                privilege_row["role_name"],
                roles_dict[role_id_str].privileges + (
                    Privilege(privilege_row["privilege_id"],
                              privilege_row["privilege_description"]),))
        }

    return {
        **roles_dict,
        role_id_str: Role(
            UUID(role_id_str),
            privilege_row["role_name"],
            (Privilege(privilege_row["privilege_id"],
                       privilege_row["privilege_description"]),))
    }

def user_roles(conn: db.DbConnection, user: User) -> Maybe[Sequence[Role]]:
    """Retrieve non-resource roles assigned to the user."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "SELECT r.*, p.* FROM user_roles AS ur INNER JOIN roles AS r "
            "ON ur.role_id=r.role_id INNER JOIN role_privileges AS rp "
            "ON r.role_id=rp.role_id INNER JOIN privileges AS p "
            "ON rp.privilege_id=p.privilege_id WHERE ur.user_id=?",
            (str(user.user_id),))

        results = cursor.fetchall()
        if results:
            return Just(tuple(
                reduce(__organise_privileges__, results, {}).values()))
        return Nothing

def assign_default_roles(cursor: db.DbCursor, user: User):
    """Assign `user` some default roles."""
    cursor.execute(
        'SELECT role_id FROM roles WHERE role_name IN '
        '("group-creator")')
    role_ids = cursor.fetchall()
    str_user_id = str(user.user_id)
    params = tuple(
        {"user_id": str_user_id, "role_id": row["role_id"]} for row in role_ids)
    cursor.executemany(
        ("INSERT INTO user_roles VALUES (:user_id, :role_id)"),
        params)
