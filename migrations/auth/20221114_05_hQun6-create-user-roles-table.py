"""
Create 'user_roles' table.
"""

from yoyo import step

__depends__ = {'20221114_04_tLUzB-initialise-basic-roles'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS user_roles(
            user_id TEXT NOT NULL,
            role_id TEXT NOT NULL,
            PRIMARY KEY(user_id, role_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
              ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY(role_id) REFERENCES roles(role_id)
              ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS user_roles"),
    step(
        """
        CREATE INDEX IF NOT EXISTS idx_tbl_user_roles_cols_user_id
        ON user_roles(user_id)
        """,
        "DROP INDEX IF EXISTS idx_tbl_user_roles_cols_user_id")
]
