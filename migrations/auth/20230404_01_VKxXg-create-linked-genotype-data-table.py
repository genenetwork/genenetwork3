"""
Create linked genotype data table
"""

from yoyo import step

__depends__ = {'20230322_02_Ll854-create-phenotype-resources-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS linked_genotype_data
        -- Link genotype data in MariaDB to user groups in auth system
        (
          data_link_id TEXT NOT NULL PRIMARY KEY, -- A new ID for the auth system
          group_id TEXT NOT NULL, -- The user group the data is linked to
          SpeciesId TEXT NOT NULL, -- The species in MariaDB
          InbredSetId TEXT NOT NULL, -- The traits group in MariaDB
          GenoFreezeId TEXT NOT NULL, -- The dataset Id in MariaDB
          dataset_name TEXT, -- dataset Name in MariaDB
          dataset_fullname, -- dataset FullName in MariaDB
          dataset_shortname, -- dataset ShortName in MariaDB
          FOREIGN KEY (group_id)
            REFERENCES groups(group_id) ON UPDATE CASCADE ON DELETE RESTRICT
          UNIQUE (SpeciesId, InbredSetId, GenoFreezeId)
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS linked_genotype_data")
]
