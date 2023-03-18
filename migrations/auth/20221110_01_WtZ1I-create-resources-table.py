"""
Create 'resources' table
"""

from yoyo import step

__depends__ = {'20221109_01_HbD5F-add-resource-meta-field-to-resource-categories-field'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS resources(
            group_id TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            resource_name TEXT NOT NULL UNIQUE,
            resource_category_id TEXT NOT NULL,
            PRIMARY KEY(group_id, resource_id),
            FOREIGN KEY(group_id) REFERENCES groups(group_id)
              ON UPDATE CASCADE ON DELETE RESTRICT,
            FOREIGN KEY(resource_category_id)
              REFERENCES resource_categories(resource_category_id)
              ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS resources")
]
