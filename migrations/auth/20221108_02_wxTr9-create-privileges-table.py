"""
Create privileges table
"""

from yoyo import step

__depends__ = {'20221108_01_CoxYh-create-the-groups-table'}

steps = [
    step(
        """
        CREATE TABLE privileges(
            privilege_id TEXT PRIMARY KEY,
            privilege_name TEXT NOT NULL
        ) WITHOUT ROWID
        """,
         "DROP TABLE IF EXISTS privileges")
]
