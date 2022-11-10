"""Test that indexes are created and removed."""

from contextlib import closing

import pytest
import sqlite3

from gn3.migrations import get_migration, apply_migrations, rollback_migrations
from tests.unit.auth.conftest import (
    apply_single_migration, rollback_single_migration, migrations_up_to)

query = """
SELECT name FROM sqlite_master WHERE type='index' AND tbl_name = ?
AND name= ?
"""

migrations_tables_and_indexes = (
    ("20221110_05_BaNtL-create-roles-table.py", "roles",
     "idx_tbl_roles_cols_group_id"),)

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "migration_file,the_table,the_index", migrations_tables_and_indexes)
def test_index_created(
        auth_testdb_path, auth_migrations_dir, backend, migration_file,
        the_table, the_index):
    """
    GIVEN: A database migration
    WHEN: The migration is applied
    THEN: Ensure the given index is created for the provided table
    """
    migration_path=f"{auth_migrations_dir}/{migration_file}"
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    the_migration = get_migration(migration_path)
    query_params = (the_table, the_index)
    apply_migrations(backend, older_migrations)
    with closing(sqlite3.connect(auth_testdb_path)) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(query, query_params)
        result_before_migration = cursor.fetchall()
        apply_single_migration(backend, the_migration)
        cursor.execute(query, query_params)
        result_after_migration = cursor.fetchall()

    rollback_migrations(backend, older_migrations + [the_migration])
    assert the_index not in [row[0] for row in result_before_migration], (
        f"Index '{the_index}' was not found for table '{the_table}'.")
    assert (
        len(result_after_migration) == 1
        and result_after_migration[0][0] == the_index), (
        f"Index '{the_index}' was not found for table '{the_table}'.")

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "migration_file,the_table,the_index", migrations_tables_and_indexes)
def test_index_dropped(
        auth_testdb_path, auth_migrations_dir, backend, migration_file,
        the_table, the_index):
    """
    GIVEN: A database migration
    WHEN: The migration is rolled-back
    THEN: Ensure the given index no longer exists for the given table
    """
    migration_path=f"{auth_migrations_dir}/{migration_file}"
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    the_migration = get_migration(migration_path)
    query_params = (the_table, the_index)
    apply_migrations(backend, older_migrations)
    with closing(sqlite3.connect(auth_testdb_path)) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(query, query_params)
        result_before_migration = cursor.fetchall()
        apply_single_migration(backend, the_migration)
        cursor.execute(query, query_params)
        result_after_migration = cursor.fetchall()
        rollback_single_migration(backend, the_migration)
        cursor.execute(query, query_params)
        result_after_rollback = cursor.fetchall()

    rollback_migrations(backend, older_migrations)
    assert the_index not in [row[0] for row in result_before_migration], (
        f"Index '{the_index}' was found for table '{the_table}' before "
        "migration")
    assert (
        len(result_after_migration) == 1
        and result_after_migration[0][0] == the_index), (
        f"Index '{the_index}' was not found for table '{the_table}'.")
    assert the_index not in [row[0] for row in result_after_rollback], (
        f"Index '{the_index}' was found for table '{the_table}' after "
        "rollback")
