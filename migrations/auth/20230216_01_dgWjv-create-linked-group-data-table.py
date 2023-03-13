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
          dataset_type TEXT NOT NULL,
          dataset_or_trait_id TEXT NOT NULL,
          dataset_name TEXT NOT NULL,
          dataset_fullname TEXT NOT NULL,
          accession_id TEXT DEFAULT NULL,
          PRIMARY KEY(group_id, dataset_type, dataset_or_trait_id),
          FOREIGN KEY (group_id) REFERENCES groups(group_id)
            ON UPDATE CASCADE ON DELETE RESTRICT,
          CHECK (dataset_type IN ('mRNA', 'Genotype', 'Phenotype'))
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS linked_group_data")
]