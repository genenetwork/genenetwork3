"""
Modify 'group_roles': add 'group_role_id'

At this point, there is no data in the `group_roles` table  and therefore, it
should be safe to simply recreate it.
"""

from yoyo import step

__depends__ = {'20221116_01_nKUmX-add-privileges-to-group-leader-role'}

steps = [
    step(
        "DROP INDEX IF EXISTS idx_tbl_group_roles_cols_group_id",
        """
        CREATE INDEX IF NOT EXISTS idx_tbl_group_roles_cols_group_id
        ON group_roles(group_id)
        """),
    step(
        "DROP TABLE IF EXISTS group_roles",
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
        """),
    step(
        """
        CREATE TABLE IF NOT EXISTS group_roles(
            group_role_id TEXT PRIMARY KEY,
            group_id TEXT NOT NULL,
            role_id TEXT NOT NULL,
            UNIQUE (group_id, role_id),
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
