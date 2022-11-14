"""Handle privileges"""
from uuid import UUID

from gn3.auth import db

def user_privileges(conn, user_id: UUID):
    """Fetch the user's privileges from the database."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            ("SELECT p.privilege_name "
             "FROM user_roles AS ur "
             "INNER JOIN role_privileges AS rp ON ur.role_id=rp.role_id "
             "INNER JOIN privileges AS p ON rp.privilege_id=p.privilege_id "
             "WHERE ur.user_id=?"),
            (str(user_id),))
        return tuple(row[0] for row in cursor.fetchall())
