"""
Test that the `resource_categories` table is initialised with the startup data.
"""
from contextlib import closing

import pytest
import sqlite3

from gn3.migrations import get_migration, apply_migrations, rollback_migrations
from tests.unit.auth.conftest import (
    apply_single_migration, rollback_single_migration, migrations_up_to)

migration_path = "migrations/auth/20221108_04_CKcSL-init-data-in-resource-categories-table.py"

@pytest.mark.unit_test
def test_apply_init_data(auth_testdb_path, auth_migrations_dir, backend):
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    the_migration = get_migration(migration_path)
    apply_migrations(backend, older_migrations)
    with closing(sqlite3.connect(auth_testdb_path)) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT * FROM resource_categories")
        assert len(cursor.fetchall()) == 0, "Expected empty table."
        apply_single_migration(backend, the_migration)
        cursor.execute("SELECT * FROM resource_categories")
        results = cursor.fetchall()
        assert len(results) == 3, "Expected 3 rows of data."
        assert sorted(results) == sorted((
            ('fad071a3-2fc8-40b8-992b-cdefe7dcac79', 'mrna', 'mRNA Dataset'),
            ('548d684b-d4d1-46fb-a6d3-51a56b7da1b3', 'phenotype',
             'Phenotype (Publish) Dataset'),
            ('48056f84-a2a6-41ac-8319-0e1e212cba2a', 'genotype',
             'Genotype Dataset')))

    rollback_migrations(backend, older_migrations + [the_migration])

@pytest.mark.unit_test
def test_rollback_init_data(auth_testdb_path, auth_migrations_dir, backend):
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    the_migration = get_migration(migration_path)
    apply_migrations(backend, older_migrations)
    with closing(sqlite3.connect(auth_testdb_path)) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT * FROM resource_categories")
        assert len(cursor.fetchall()) == 0, "Expected empty table."
        apply_single_migration(backend, the_migration)
        cursor.execute("SELECT * FROM resource_categories")
        results = cursor.fetchall()
        assert len(results) == 3, "Expected 3 rows of data."
        rollback_single_migration(backend, the_migration)
        cursor.execute("SELECT * FROM resource_categories")
        assert len(cursor.fetchall()) == 0, "Expected empty table."

    rollback_migrations(backend, older_migrations)
