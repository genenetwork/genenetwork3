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
          group_id TEXT NOT NULL,
          resource_id TEXT NOT NULL, -- A resource can have multiple items
          data_link_id TEXT NOT NULL,
          PRIMARY KEY (group_id, resource_id, data_link_id),
          UNIQUE (data_link_id) -- ensure data is linked to single resource
          FOREIGN KEY (group_id, resource_id)
            REFERENCES resources(group_id, resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (data_link_id)
            REFERENCES linked_genotype_data(data_link_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS genotype_resources")
]
