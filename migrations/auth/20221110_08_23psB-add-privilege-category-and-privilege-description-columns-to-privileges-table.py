"""
Add 'privilege_category' and 'privilege_description' columns to 'privileges' table
"""

from yoyo import step

__depends__ = {'20221110_07_7WGa1-create-role-privileges-table'}

steps = [
    step(
        """
        ALTER TABLE privileges ADD COLUMN
            privilege_category TEXT NOT NULL DEFAULT 'common'
        """,
        "ALTER TABLE privileges DROP COLUMN privilege_category"),
    step(
        """
        ALTER TABLE privileges ADD COLUMN
            privilege_description TEXT
        """,
        "ALTER TABLE privileges DROP COLUMN privilege_description")
]
