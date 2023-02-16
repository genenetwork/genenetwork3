"""
Create linked_group_data table
"""

from yoyo import step

__depends__ = {'20230210_02_lDK14-create-system-admin-role'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS linked_group_data(
          group_id TEXT NOT NULL,
          dataset_or_trait_id TEXT NOT NULL,
          name TEXT NOT NULL,
          type TEXT NOT NULL,
          PRIMARY KEY(group_id, dataset_or_trait_id),
          FOREIGN KEY (group_id) REFERENCES groups(group_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          CHECK (type IN ('mRNA', 'Genotype', 'Phenotype'))
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS linked_group_data")
]
