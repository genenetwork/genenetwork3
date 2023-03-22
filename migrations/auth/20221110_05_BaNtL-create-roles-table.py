"""
Create 'roles' table
"""

from yoyo import step

__depends__ = {'20221110_01_WtZ1I-create-resources-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS roles(
            role_id TEXT NOT NULL PRIMARY KEY,
            role_name TEXT NOT NULL,
            user_editable INTEGER NOT NULL DEFAULT 1 CHECK (user_editable=0 or user_editable=1)
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS roles")
]
