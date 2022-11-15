"""Handle management of roles"""
from uuid import UUID, uuid4
from typing import Iterable, NamedTuple

from gn3.auth import db

from .checks import authorised_p
from .privileges import Privilege

class Role(NamedTuple):
    """Class representing a role: creates immutable objects."""
    role_id: UUID
    role_name: str
    privileges: Iterable[Privilege]

@authorised_p(("create-role",), error_message="Could not create role")
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
        (role.role_id, role.role_name))
    cursor.execute(
        "INSERT INTO role_privileges(role_id, privilege_id) VALUES (?, ?)",
        ((role.role_id, priv.privilege_id) for priv in privileges))

    return role
