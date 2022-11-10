"""
Create 'generic_roles' table

The roles in this table will be template roles, defining some common roles that
can be used within the groups.

They could also be used to define system-level roles, though those will not be
provided to the "common" users.
"""

from yoyo import step

__depends__ = {'20221110_05_BaNtL-create-roles-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS generic_roles(
            role_id TEXT PRIMARY KEY,
            role_name TEXT NOT NULL
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS generic_roles")
]
