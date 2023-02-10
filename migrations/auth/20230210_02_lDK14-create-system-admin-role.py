"""
Create system-admin role
"""
import uuid
from contextlib import closing

from yoyo import step

__depends__ = {'20230210_01_8xMa1-system-admin-privileges-for-data-distribution'}

def create_sys_admin_role(conn):
    with closing(conn.cursor()) as cursor:
        role_id = uuid.uuid4()
        cursor.execute(
            "INSERT INTO roles VALUES (?, 'system-administrator', '0')",
            (str(role_id),))

        cursor.executemany(
            "INSERT INTO role_privileges VALUES (:role_id, :privilege_id)",
            ({"role_id": f"{role_id}", "privilege_id": priv}
         for priv in (
                 "system:data:link-to-group",
                 "system:group:create-group",
                 "system:group:delete-group",
                 "system:group:edit-group",
                 "system:group:transfer-group-leader",
                 "system:group:view-group",
                 "system:user:assign-group-leader",
                 "system:user:delete-user",
                 "system:user:masquerade",
                 "system:user:reset-password")))

def drop_sys_admin_role(conn):
    pass

steps = [
    step(create_sys_admin_role, drop_sys_admin_role)
]
