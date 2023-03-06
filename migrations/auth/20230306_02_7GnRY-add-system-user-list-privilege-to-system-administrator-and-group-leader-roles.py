"""
Add system:user:list privilege to system-administrator and group-leader roles.
"""
import uuid
import contextlib

from yoyo import step

__depends__ = {'20230306_01_pRfxl-add-system-user-list-privilege'}

def role_ids(cursor):
    """Get role ids from names"""
    cursor.execute(
        "SELECT * FROM roles WHERE role_name IN "
        "('system-administrator', 'group-leader')")
    return (uuid.UUID(row[0]) for row in cursor.fetchall())

def add_privilege_to_roles(conn):
    """
    Add 'system:user:list' privilege to 'system-administrator' and
    'group-leader' roles."""
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.executemany(
            "INSERT INTO role_privileges(role_id,privilege_id) "
            "VALUES(?, ?)",
            tuple((str(role_id), "system:user:list")
                  for role_id in role_ids(cursor)))

def del_privilege_from_roles(conn):
    """
    Delete 'system:user:list' privilege to 'system-administrator' and
    'group-leader' roles.
    """
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute(
            "DELETE FROM role_privileges WHERE "
            "role_id IN (?, ?) AND privilege_id='system:user:list'",
            tuple(str(role_id) for role_id in role_ids(cursor)))

steps = [
    step(add_privilege_to_roles, del_privilege_from_roles)
]
