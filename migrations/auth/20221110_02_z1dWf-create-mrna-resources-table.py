"""
Create 'mrna_resources' table

NOTE: One "mRNA dataset" should only ever be linked to one and only one resource object.
      One "resource object" should only ever be linked to one and only one "mRNA dataset".
"""

from yoyo import step

__depends__ = {'20221110_01_WtZ1I-create-resources-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS mrna_resources(
            resource_id TEXT PRIMARY KEY,
            dataset_id TEXT NOT NULL UNIQUE,
            FOREIGN KEY(resource_id) REFERENCES resources(resource_id)
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS mrna_resources")
]
