"""
Create phenotype_resources table
"""

from yoyo import step

__depends__ = {'20230322_01_0dDZR-create-linked-phenotype-data-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS phenotype_resources
        -- Link phenotype data to specific resources
        (
          resource_id TEXT NOT NULL, -- A resource can have multiple data items
          data_link_id TEXT NOT NULL,
          PRIMARY KEY(resource_id, data_link_id),
          UNIQUE (data_link_id) -- ensure data is linked to only one resource
        )
        """,
        "DROP TABLE IF EXISTS phenotype_resources")
]
