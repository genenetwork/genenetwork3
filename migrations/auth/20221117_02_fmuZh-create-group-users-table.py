"""
Create 'group_users' table.
"""

from yoyo import step

__depends__ = {'20221117_01_RDlfx-modify-group-roles-add-group-role-id'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS group_users(
            group_id TEXT NOT NULL,
            user_id TEXT NOT NULL UNIQUE, -- user can only be in one group
            PRIMARY KEY(group_id, user_id)
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS group_users"),
    step(
        """
        CREATE INDEX IF NOT EXISTS tbl_group_users_cols_group_id
        ON group_users(group_id)
        """,
        "DROP INDEX IF EXISTS tbl_group_users_cols_group_id")
]
