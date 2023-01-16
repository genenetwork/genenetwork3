"""Handle privileges"""
from typing import Iterable, NamedTuple

from gn3.auth import db
from gn3.auth.authentication.users import User

class Privilege(NamedTuple):
    """Class representing a privilege: creates immutable objects."""
    privilege_id: str
    privilege_description: str

def user_privileges(conn: db.DbConnection, user: User) -> Iterable[Privilege]:
    """Fetch the user's privileges from the database."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            ("SELECT p.privilege_id, p.privilege_description "
             "FROM user_roles AS ur "
             "INNER JOIN role_privileges AS rp ON ur.role_id=rp.role_id "
             "INNER JOIN privileges AS p ON rp.privilege_id=p.privilege_id "
             "WHERE ur.user_id=?"),
            (str(user.user_id),))
        results = cursor.fetchall()

    return (Privilege(row[0], row[1]) for row in results)
