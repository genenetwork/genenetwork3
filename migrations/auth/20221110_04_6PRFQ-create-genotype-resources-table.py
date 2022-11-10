"""
Create 'genotype_resources' table

NOTE: A "genotype resource" can only ever be linked to one and only one "resource object"
      A "resource object" can be linked to one or more "genotype resource".
"""

from yoyo import step

__depends__ = {'20221110_03_ka3W0-create-phenotype-resources-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS genotype_resources(
            resource_id TEXT NOT NULL,
            trait_id TEXT NOT NULL UNIQUE,
            PRIMARY KEY(resource_id, trait_id),
            FOREIGN KEY(resource_id) REFERENCES resources(resource_id)
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS genotype_resources")
]
