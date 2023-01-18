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
            group_id TEXT NOT NULL,
            resource_id TEXT NOT NULL,
            trait_id TEXT NOT NULL UNIQUE,
            PRIMARY KEY(resource_id, trait_id),
            FOREIGN KEY(group_id, resource_id)
              REFERENCES resources(group_id, resource_id)
              ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS phenotype_resources")
]
