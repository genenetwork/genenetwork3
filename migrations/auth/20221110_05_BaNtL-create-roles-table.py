"""
Create 'roles' table
"""

from yoyo import step

__depends__ = {'20221110_04_6PRFQ-create-genotype-resources-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS roles(
            role_id TEXT NOT NULL PRIMARY KEY,
            role_name TEXT NOT NULL
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS roles")
]
