"""
Add system:user:list privilege
"""
import contextlib

from yoyo import step

__depends__ = {'20230210_02_lDK14-create-system-admin-role'}

def insert_users_list_priv(conn):
    """Create a new 'system:user:list' privilege."""
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute(
            "INSERT INTO privileges(privilege_id, privilege_description) "
            "VALUES('system:user:list', 'List users in the system') "
            "ON CONFLICT (privilege_id) DO NOTHING")

def delete_users_list_priv(conn):
    """Delete the new 'system:user:list' privilege."""
    with contextlib.closing(conn.cursor()) as cursor:
        cursor.execute(
            "DELETE FROM privileges WHERE privilege_id='system:user:list'")

steps = [
    step(insert_users_list_priv, delete_users_list_priv)
]
