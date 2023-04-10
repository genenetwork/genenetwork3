"""
Create linked mrna data table
"""

from yoyo import step

__depends__ = {'20230404_02_la33P-create-genotype-resources-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS linked_mrna_data
        -- Link mRNA Assay data in MariaDB to user groups in auth system
        (
          data_link_id TEXT NOT NULL PRIMARY KEY, -- A new ID for the auth system
          group_id TEXT NOT NULL, -- The user group the data is linked to
          SpeciesId TEXT NOT NULL, -- The species in MariaDB
          InbredSetId TEXT NOT NULL, -- The traits group in MariaDB
          ProbeFreezeId TEXT NOT NULL, -- The study ID in MariaDB
          ProbeSetFreezeId TEXT NOT NULL, -- The dataset Id in MariaDB
          dataset_name TEXT, -- dataset Name in MariaDB
          dataset_fullname, -- dataset FullName in MariaDB
          dataset_shortname, -- dataset ShortName in MariaDB
          FOREIGN KEY (group_id)
            REFERENCES groups(group_id) ON UPDATE CASCADE ON DELETE RESTRICT
          UNIQUE (SpeciesId, InbredSetId, ProbeFreezeId, ProbeSetFreezeId)
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS linked_mrna_data")
]
