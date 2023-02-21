"""
Make dataset_id and trait_id foreign keys in tables

This migration makes dataset_id and trait_id columns FOREIGN KEYS in the tables:

* mrna_resources
* genotype_resources
* phenotype_resources

At this point, there really should be no data in the table, so it should not
cause issues, but since this will be run by humans, there is a chance that
unexpected actions might be taken, so this code takes a somewhat deliberate
extra step to ensure the integrity of data is maintained.
"""
from contextlib import closing

from yoyo import step

def add_foreign_key_to_mrna_resources(conn):
    """Make `dataset_id` a foreign key in mrna_resources."""
    with closing(conn.cursor()) as cursor:
        cursor.execute(
            "ALTER TABLE mrna_resources RENAME TO mrna_resources_bkp")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mrna_resources(
              group_id TEXT NOT NULL,
              resource_id TEXT PRIMARY KEY,
              dataset_type TEXT NOT NULL DEFAULT "mRNA"
                CHECK (dataset_type="mRNA"),
              dataset_id TEXT NOT NULL UNIQUE,
              FOREIGN KEY(group_id, resource_id)
                REFERENCES resources(group_id, resource_id)
                ON UPDATE CASCADE ON DELETE RESTRICT,
              FOREIGN KEY (group_id, dataset_type, dataset_id)
                REFERENCES
                  linked_group_data(group_id, dataset_type, dataset_or_trait_id)
                ON UPDATE CASCADE ON DELETE CASCADE
              ) WITHOUT ROWID
            """)
        cursor.execute(
            "SELECT group_id, resource_id, dataset_id FROM mrna_resources_bkp")
        rows = ((row[0], row[1], row[2]) for row in cursor.fetchall())
        cursor.executemany(
            "INSERT INTO mrna_resources(group_id, resource_id, dataset_id) "
            "VALUES (?, ?, ?)",
            rows)
        cursor.execute("DROP TABLE mrna_resources_bkp")

def drop_foreign_key_from_mrna_resources(conn):
    """Undo `add_foreign_key_to_mrna_resources` above."""
    with closing(conn.cursor()) as cursor:
        cursor.execute(
            "ALTER TABLE mrna_resources RENAME TO mrna_resources_bkp")
        cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS mrna_resources(
          group_id TEXT NOT NULL,
          resource_id TEXT PRIMARY KEY,
          dataset_id TEXT NOT NULL UNIQUE,
          FOREIGN KEY(group_id, resource_id)
            REFERENCES resources(group_id, resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)
        cursor.execute(
            "SELECT group_id, resource_id, dataset_id FROM mrna_resources_bkp")
        rows = ((row[0], row[1], row[2]) for row in cursor.fetchall())
        cursor.executemany(
            "INSERT INTO mrna_resources(group_id, resource_id, dataset_id) "
            "VALUES (?, ?, ?)",
            rows)
        cursor.execute("DROP TABLE mrna_resources_bkp")

def add_foreign_key_to_geno_resources(conn):
    """Make `trait_id` a foreign key in genotype_resources."""
    with closing(conn.cursor()) as cursor:
        cursor.execute(
            "ALTER TABLE genotype_resources RENAME TO genotype_resources_bkp")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS genotype_resources(
              group_id TEXT NOT NULL,
              resource_id TEXT PRIMARY KEY,
              dataset_type TEXT NOT NULL DEFAULT "Genotype"
                CHECK (dataset_type="Genotype"),
              trait_id TEXT NOT NULL UNIQUE,
              FOREIGN KEY(group_id, resource_id)
                REFERENCES resources(group_id, resource_id)
                ON UPDATE CASCADE ON DELETE RESTRICT,
              FOREIGN KEY (group_id, dataset_type, trait_id)
                REFERENCES
                  linked_group_data(group_id, dataset_type, dataset_or_trait_id)
                ON UPDATE CASCADE ON DELETE CASCADE
              ) WITHOUT ROWID
            """)
        cursor.execute(
            "SELECT group_id, resource_id, trait_id "
            "FROM genotype_resources_bkp")
        rows = ((row[0], row[1], row[2]) for row in cursor.fetchall())
        cursor.executemany(
            "INSERT INTO genotype_resources(group_id, resource_id, trait_id) "
            "VALUES (?, ?, ?)",
            rows)
        cursor.execute("DROP TABLE genotype_resources_bkp")

def drop_foreign_key_from_geno_resources(conn):
    """Undo `add_foreign_key_to_geno_resources` above."""
    with closing(conn.cursor()) as cursor:
        cursor.execute(
            "ALTER TABLE genotype_resources RENAME TO genotype_resources_bkp")
        cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS genotype_resources(
          group_id TEXT NOT NULL,
          resource_id TEXT PRIMARY KEY,
          trait_id TEXT NOT NULL UNIQUE,
          FOREIGN KEY(group_id, resource_id)
            REFERENCES resources(group_id, resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)
        cursor.execute(
            "SELECT group_id, resource_id, trait_id "
            "FROM genotype_resources_bkp")
        rows = ((row[0], row[1], row[2]) for row in cursor.fetchall())
        cursor.executemany(
            "INSERT INTO genotype_resources(group_id, resource_id, trait_id) "
            "VALUES (?, ?, ?)",
            rows)
        cursor.execute("DROP TABLE genotype_resources_bkp")

def add_foreign_key_to_pheno_resources(conn):
    """Make `trait_id` a foreign key in phenotype_resources."""
    with closing(conn.cursor()) as cursor:
        cursor.execute(
            "ALTER TABLE phenotype_resources RENAME TO phenotype_resources_bkp")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS phenotype_resources(
              group_id TEXT NOT NULL,
              resource_id TEXT PRIMARY KEY,
              dataset_type TEXT NOT NULL DEFAULT "Phenotype"
                CHECK (dataset_type="Phenotype"),
              trait_id TEXT NOT NULL UNIQUE,
              FOREIGN KEY(group_id, resource_id)
                REFERENCES resources(group_id, resource_id)
                ON UPDATE CASCADE ON DELETE RESTRICT,
              FOREIGN KEY (group_id, dataset_type, trait_id)
                REFERENCES
                  linked_group_data(group_id, dataset_type, dataset_or_trait_id)
                ON UPDATE CASCADE ON DELETE CASCADE
              ) WITHOUT ROWID
            """)
        cursor.execute(
            "SELECT group_id, resource_id, trait_id "
            "FROM phenotype_resources_bkp")
        rows = ((row[0], row[1], row[2]) for row in cursor.fetchall())
        cursor.executemany(
            "INSERT INTO phenotype_resources(group_id, resource_id, trait_id) "
            "VALUES (?, ?, ?)",
            rows)
        cursor.execute("DROP TABLE phenotype_resources_bkp")

def drop_foreign_key_from_pheno_resources(conn):
    """Undo `add_foreign_key_to_pheno_resources` above."""
    with closing(conn.cursor()) as cursor:
        cursor.execute(
            "ALTER TABLE phenotype_resources RENAME TO phenotype_resources_bkp")
        cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS phenotype_resources(
          group_id TEXT NOT NULL,
          resource_id TEXT PRIMARY KEY,
          trait_id TEXT NOT NULL UNIQUE,
          FOREIGN KEY(group_id, resource_id)
            REFERENCES resources(group_id, resource_id)
            ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """)
        cursor.execute(
            "SELECT group_id, resource_id, trait_id "
            "FROM phenotype_resources_bkp")
        rows = ((row[0], row[1], row[2]) for row in cursor.fetchall())
        cursor.executemany(
            "INSERT INTO phenotype_resources(group_id, resource_id, trait_id) "
            "VALUES (?, ?, ?)",
            rows)
        cursor.execute("DROP TABLE phenotype_resources_bkp")

from yoyo import step

__depends__ = {'20230216_01_dgWjv-create-linked-group-data-table'}

steps = [
    step(add_foreign_key_to_mrna_resources,
         drop_foreign_key_from_mrna_resources),
    step(add_foreign_key_to_geno_resources,
         drop_foreign_key_from_geno_resources),
    step(add_foreign_key_to_pheno_resources,
         drop_foreign_key_from_pheno_resources)
]
