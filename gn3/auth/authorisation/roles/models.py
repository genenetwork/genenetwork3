"""Handle management of roles"""
from uuid import UUID, uuid4
from functools import reduce
from typing import Any, Sequence, Iterable, NamedTuple

from pymonad.either import Left, Right, Either

from gn3.auth import db
from gn3.auth.dictify import dictify
from gn3.auth.authentication.users import User
from gn3.auth.authorisation.errors import AuthorisationError

from ..checks import authorised_p
from ..privileges import Privilege
from ..errors import NotFoundError

class Role(NamedTuple):
    """Class representing a role: creates immutable objects."""
    role_id: UUID
    role_name: str
    user_editable: bool
    privileges: tuple[Privilege, ...]

    def dictify(self) -> dict[str, Any]:
        """Return a dict representation of `Role` objects."""
        return {
            "role_id": self.role_id, "role_name": self.role_name,
            "user_editable": self.user_editable,
            "privileges": tuple(dictify(priv) for priv in self.privileges)
        }

def check_user_editable(role: Role):
    """Raise an exception if `role` is not user editable."""
    if not role.user_editable:
        raise AuthorisationError(
            f"The role `{role.role_name}` is not user editable.")

@authorised_p(
    privileges = ("group:role:create-role",),
    error_description="Could not create role")
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
    role = Role(uuid4(), role_name, True, tuple(privileges))

    cursor.execute(
        "INSERT INTO roles(role_id, role_name, user_editable) VALUES (?, ?, ?)",
        (str(role.role_id), role.role_name, (1 if role.user_editable else 0)))
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
                bool(int(privilege_row["user_editable"])),
                roles_dict[role_id_str].privileges + (
                    Privilege(privilege_row["privilege_id"],
                              privilege_row["privilege_description"]),))
        }

    return {
        **roles_dict,
        role_id_str: Role(
            UUID(role_id_str),
            privilege_row["role_name"],
            bool(int(privilege_row["user_editable"])),
            (Privilege(privilege_row["privilege_id"],
                       privilege_row["privilege_description"]),))
    }

def user_roles(conn: db.DbConnection, user: User) -> Sequence[Role]:
    """Retrieve non-resource roles assigned to the user."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "SELECT r.*, p.* FROM user_roles AS ur INNER JOIN roles AS r "
            "ON ur.role_id=r.role_id INNER JOIN role_privileges AS rp "
            "ON r.role_id=rp.role_id INNER JOIN privileges AS p "
            "ON rp.privilege_id=p.privilege_id WHERE ur.user_id=?",
            (str(user.user_id),))

        return tuple(
            reduce(__organise_privileges__, cursor.fetchall(), {}).values())
    return tuple()

def user_role(conn: db.DbConnection, user: User, role_id: UUID) -> Either:
    """Retrieve a specific non-resource role assigned to the user."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "SELECT r.*, p.* FROM user_roles AS ur INNER JOIN roles AS r "
            "ON ur.role_id=r.role_id INNER JOIN role_privileges AS rp "
            "ON r.role_id=rp.role_id INNER JOIN privileges AS p "
            "ON rp.privilege_id=p.privilege_id "
            "WHERE ur.user_id=? AND ur.role_id=?",
            (str(user.user_id), str(role_id)))

        results = cursor.fetchall()
        if results:
            return Right(tuple(
                reduce(__organise_privileges__, results, {}).values())[0])
        return Left(NotFoundError(
            f"Could not find role with id '{role_id}'",))

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

def revoke_user_role_by_name(cursor: db.DbCursor, user: User, role_name: str):
    """Revoke a role from `user` by the role's name"""
    cursor.execute(
        "SELECT role_id FROM roles WHERE role_name=:role_name",
        {"role_name": role_name})
    role = cursor.fetchone()
    if role:
        cursor.execute(
            ("DELETE FROM user_roles "
             "WHERE user_id=:user_id AND role_id=:role_id"),
            {"user_id": str(user.user_id), "role_id": role["role_id"]})

def assign_user_role_by_name(cursor: db.DbCursor, user: User, role_name: str):
    """Revoke a role from `user` by the role's name"""
    cursor.execute(
        "SELECT role_id FROM roles WHERE role_name=:role_name",
        {"role_name": role_name})
    role = cursor.fetchone()

    if role:
        cursor.execute(
            ("INSERT INTO user_roles VALUES(:user_id, :role_id) "
             "ON CONFLICT DO NOTHING"),
            {"user_id": str(user.user_id), "role_id": role["role_id"]})
