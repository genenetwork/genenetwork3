"""
Create mRNA resources table
"""

from yoyo import step

__depends__ = {'20230410_01_8mwaf-create-linked-mrna-data-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS mrna_resources
        -- Link mRNA data to specific resource
        (
          group_id TEXT NOT NULL,
          resource_id TEXT NOT NULL, -- A resource can have multiple items
          data_link_id TEXT NOT NULL,
          PRIMARY KEY (resource_id, data_link_id),
          UNIQUE (data_link_id) -- ensure data is linked to single resource
          FOREIGN KEY (group_id, resource_id)
            REFERENCES resources(group_id, resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          FOREIGN KEY (data_link_id) REFERENCES linked_mrna_data(data_link_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS mrna_resources")
]
