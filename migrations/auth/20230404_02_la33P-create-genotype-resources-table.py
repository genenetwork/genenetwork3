"""
Create genotype resources table
"""

from yoyo import step

__depends__ = {'20230404_01_VKxXg-create-linked-genotype-data-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS genotype_resources
        -- Link genotype data to specific resource
        (
          resource_id TEXT NOT NULL, -- A resource can have multiple items
          data_link_id TEXT NOT NULL,
          PRIMARY KEY (resource_id, data_link_id),
          UNIQUE (data_link_id) -- ensure data is linked to single resource
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS genotype_resources")
]
