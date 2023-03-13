"""
Drop 'generic_role*' tables
"""

from yoyo import step

__depends__ = {'20221114_01_n8gsF-create-generic-role-privileges-table'}

steps = [
    step(
        """
        DROP INDEX IF EXISTS
            idx_tbl_generic_role_privileges_cols_generic_role_id
        """,
        """
        CREATE INDEX IF NOT EXISTS
            idx_tbl_generic_role_privileges_cols_generic_role_id
        ON generic_role_privileges(generic_role_id)
        """),
    step(
        "DROP TABLE IF EXISTS generic_role_privileges",
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
        """),
    step(
        "DROP TABLE IF EXISTS generic_roles",
        """
        CREATE TABLE IF NOT EXISTS generic_roles(
            role_id TEXT PRIMARY KEY,
            role_name TEXT NOT NULL
        ) WITHOUT ROWID
        """)
]
