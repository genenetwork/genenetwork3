"""
Add 'resource_meta' field to 'resource_categories' field.
"""

from yoyo import step

__depends__ = {'20221108_04_CKcSL-init-data-in-resource-categories-table'}

steps = [
    step(
        """
        ALTER TABLE resource_categories
        ADD COLUMN
            resource_meta TEXT NOT NULL DEFAULT '[]'
        """,
        "ALTER TABLE resource_categories DROP COLUMN resource_meta")
]
