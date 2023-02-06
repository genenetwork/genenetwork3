"""Test data insertion when migrations are run."""
import sqlite3
from contextlib import closing

import pytest

from gn3.migrations import get_migration, apply_migrations, rollback_migrations
from tests.unit.auth.conftest import (
    apply_single_migration, rollback_single_migration, migrations_up_to)

test_params = (
    ("20221113_01_7M0hv-enumerate-initial-privileges.py", "privileges", 19),
    ("20221114_04_tLUzB-initialise-basic-roles.py", "roles", 2),
    ("20221114_04_tLUzB-initialise-basic-roles.py", "role_privileges", 15))

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "migration_file,table,row_count", test_params)
def test_apply_insert(# pylint: disable=[too-many-arguments]
        auth_testdb_path, auth_migrations_dir, backend, migration_file,
        table, row_count):
    """
    GIVEN: A database migration
    WHEN: The migration is applied
    THEN: Ensure the given number of rows are inserted into the table
    """
    migration_path=f"{auth_migrations_dir}/{migration_file}"
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    the_migration = get_migration(migration_path)
    apply_migrations(backend, older_migrations)
    with closing(sqlite3.connect(auth_testdb_path)) as conn, closing(conn.cursor()) as cursor:
        query = f"SELECT COUNT(*) FROM {table}"
        cursor.execute(query)
        result_before_migration = cursor.fetchall()
        apply_single_migration(backend, the_migration)
        cursor.execute(query)
        result_after_migration = cursor.fetchall()

    rollback_migrations(backend, older_migrations+[the_migration])
    assert result_before_migration[0][0] == 0, (
        "Expected empty table before initialisation")
    assert result_after_migration[0][0] == row_count, (
        f"Expected {row_count} rows")

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "migration_file,table,row_count", test_params)
def test_rollback_insert(# pylint: disable=[too-many-arguments]
        auth_testdb_path, auth_migrations_dir, backend, migration_file,
        table, row_count):
    """
    GIVEN: A database migration
    WHEN: The migration is applied
    THEN: Ensure the given number of rows are inserted into the table
    """
    migration_path=f"{auth_migrations_dir}/{migration_file}"
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    the_migration = get_migration(migration_path)
    apply_migrations(backend, older_migrations)
    with closing(sqlite3.connect(auth_testdb_path)) as conn, closing(conn.cursor()) as cursor:
        query = f"SELECT COUNT(*) FROM {table}"
        cursor.execute(query)
        result_before_migration = cursor.fetchall()
        apply_single_migration(backend, the_migration)
        cursor.execute(query)
        result_after_migration = cursor.fetchall()
        rollback_single_migration(backend, the_migration)
        cursor.execute(query)
        result_after_rollback = cursor.fetchall()

    rollback_migrations(backend, older_migrations)
    assert result_before_migration[0][0] == 0, (
        "Expected empty table before initialisation")
    assert result_after_migration[0][0] == row_count, (
        f"Expected {row_count} rows")
    assert result_after_rollback[0][0] == 0, (
        "Expected empty table after rollback")
