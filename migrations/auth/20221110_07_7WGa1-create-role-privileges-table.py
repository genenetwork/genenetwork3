"""
Create 'role_privileges' table
"""

from yoyo import step

__depends__ = {'20221110_06_Pq2kT-create-generic-roles-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS role_privileges(
            role_id TEXT NOT NULL,
            privilege_id TEXT NOT NULL,
            PRIMARY KEY(role_id, privilege_id),
            FOREIGN KEY(role_id) REFERENCES roles(role_id)
              ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY(privilege_id) REFERENCES privileges(privilege_id)
              ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS role_privileges"),
    step(
        """
        CREATE INDEX IF NOT EXISTS idx_tbl_role_privileges_cols_role_id
        ON role_privileges(role_id)
        """,
        "DROP INDEX IF EXISTS idx_tbl_role_privileges_cols_role_id")
]
