"""
Create resource_categories table
"""

from yoyo import step

__depends__ = {'20221108_02_wxTr9-create-privileges-table'}

steps = [
    step(
        """
        CREATE TABLE resource_categories(
            resource_category_id TEXT PRIMARY KEY,
            resource_category_key TEXT NOT NULL,
            resource_category_description TEXT NOT NULL
        ) WITHOUT ROWID
        """,
    "DROP TABLE IF EXISTS resource_categories")
]
