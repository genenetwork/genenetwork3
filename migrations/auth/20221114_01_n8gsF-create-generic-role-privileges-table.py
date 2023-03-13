"""
Create 'generic_role_privileges' table

This table links the generic_roles to the privileges they provide
"""

from yoyo import step

__depends__ = {'20221113_01_7M0hv-enumerate-initial-privileges'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS generic_role_privileges(
            generic_role_id TEXT NOT NULL,
            privilege_id TEXT NOT NULL,
            PRIMARY KEY(generic_role_id, privilege_id),
            FOREIGN KEY(generic_role_id) REFERENCES generic_roles(role_id)
              ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY(privilege_id) REFERENCES privileges(privilege_id)
              ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS generic_role_privileges"),
    step(
        """
        CREATE INDEX IF NOT EXISTS
            idx_tbl_generic_role_privileges_cols_generic_role_id
        ON generic_role_privileges(generic_role_id)
        """,
        """
        DROP INDEX IF EXISTS
            idx_tbl_generic_role_privileges_cols_generic_role_id
        """)
]
