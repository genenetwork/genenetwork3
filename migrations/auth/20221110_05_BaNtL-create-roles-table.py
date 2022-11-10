"""
Create 'roles' table
"""

from yoyo import step

__depends__ = {'20221110_04_6PRFQ-create-genotype-resources-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS roles(
            group_id TEXT NOT NULL,
            role_id TEXT NOT NULL PRIMARY KEY,
            role_name TEXT NOT NULL,
            FOREIGN KEY(group_id) REFERENCES groups(group_id)
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS roles"),
    step(
        """
        CREATE INDEX IF NOT EXISTS idx_tbl_roles_cols_group_id
        ON roles(group_id)
        """,
        "DROP INDEX IF EXISTS idx_tbl_roles_cols_group_id")
]
