"""
Create 'group_roles' table
"""

from yoyo import step

__depends__ = {'20221114_02_DKKjn-drop-generic-role-tables'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS group_roles(
            group_id TEXT NOT NULL,
            role_id TEXT NOT NULL,
            PRIMARY KEY(group_id, role_id),
            FOREIGN KEY(group_id) REFERENCES groups(group_id)
              ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY(role_id) REFERENCES roles(role_id)
              ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS group_roles"),
    step(
        """
        CREATE INDEX IF NOT EXISTS idx_tbl_group_roles_cols_group_id
        ON group_roles(group_id)
        """,
        "DROP INDEX IF EXISTS idx_tbl_group_roles_cols_group_id")
]
