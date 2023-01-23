"""
Create the groups table
"""

from yoyo import step

__depends__ = {'20221103_02_sGrIs-create-user-credentials-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS groups(
            group_id TEXT PRIMARY KEY NOT NULL,
            group_name TEXT NOT NULL,
            group_metadata TEXT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS groups")
]
