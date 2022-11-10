"""
Create 'phenotype_resources' table

NOTE: A "phenotype resource" can only ever be linked to one and only one "resource object"
      A "resource object" can be linked to one or more "phenotype resource".
"""

from yoyo import step

__depends__ = {'20221110_02_z1dWf-create-mrna-resources-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS phenotype_resources(
            resource_id TEXT NOT NULL,
            trait_id TEXT NOT NULL UNIQUE,
            PRIMARY KEY(resource_id, trait_id),
            FOREIGN KEY(resource_id) REFERENCES resources(resource_id)
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS phenotype_resources")
]
