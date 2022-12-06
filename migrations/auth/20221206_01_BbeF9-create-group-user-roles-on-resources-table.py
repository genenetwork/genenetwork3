"""
Create 'group_user_roles_on_resources' table
"""

from yoyo import step

__depends__ = {'20221117_02_fmuZh-create-group-users-table'}

steps = [
    step(
        """
        CREATE TABLE group_user_roles_on_resources (
            group_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            role_id TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            PRIMARY KEY (group_id, user_id, role_id, resource_id),
            FOREIGN KEY (group_id, user_id)
              REFERENCES group_users(group_id, user_id),
            FOREIGN KEY (group_id, role_id)
              REFERENCES group_roles(group_id, role_id),
            FOREIGN KEY (group_id, resource_id)
              REFERENCES resources(group_id, resource_id)
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS group_user_roles_on_resources"),
    step(
        """
        CREATE INDEX IF NOT EXISTS
            idx_tbl_group_user_roles_on_resources_group_user_resource
        ON group_user_roles_on_resources(group_id, user_id, resource_id)
        """,
        """
        DROP INDEX IF EXISTS
            idx_tbl_group_user_roles_on_resources_group_user_resource""")
]
