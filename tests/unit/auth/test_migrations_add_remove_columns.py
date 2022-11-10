"""Test migrations that alter tables adding/removing columns."""

from contextlib import closing

import pytest
import sqlite3

from gn3.migrations import get_migration, apply_migrations, rollback_migrations
from tests.unit.auth.conftest import (
    apply_single_migration, rollback_single_migration, migrations_up_to)

query = "SELECT sql FROM sqlite_schema WHERE name=?"

test_params = (
    ("20221109_01_HbD5F-add-resource-meta-field-to-resource-categories-field.py",
     "resource_categories", "resource_meta TEXT", True),
    ("20221110_08_23psB-add-privilege-category-and-privilege-description-columns-to-privileges-table.py",
     "privileges", "privilege_category TEXT", True),
    ("20221110_08_23psB-add-privilege-category-and-privilege-description-columns-to-privileges-table.py",
     "privileges", "privilege_description TEXT", True))

def found(haystack: str, needle: str) -> bool:
    return any([
        (line.strip().find(needle) >= 0) for line in haystack.split("\n")])

def pristine_before_migration(adding: bool, result_str: str, column: str) -> bool:
    col_was_found = found(result_str, column)
    if adding:
        return not col_was_found
    return col_was_found

def applied_successfully(adding: bool, result_str: str, column: str) -> bool:
    col_was_found = found(result_str, column)
    if adding:
        return col_was_found
    return not col_was_found

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "migration_file,the_table,the_column,adding", test_params)
def test_apply_add_remove_column(
        auth_migrations_dir, auth_testdb_path, backend, migration_file,
        the_table, the_column, adding):
    """
    GIVEN: A migration that alters a table, adding or removing a column
    WHEN: The migration is applied
    THEN: Ensure the column exists if `adding` is True, otherwise, ensure the
          column has been dropped
    """
    migration_path = f"{auth_migrations_dir}/{migration_file}"
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    the_migration = get_migration(migration_path)
    apply_migrations(backend, older_migrations)
    with closing(sqlite3.connect(auth_testdb_path)) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(query, (the_table,))
        results_before_migration = cursor.fetchone()
        apply_single_migration(backend, the_migration)
        cursor.execute(query, (the_table,))
        results_after_migration = cursor.fetchone()

    rollback_migrations(backend, older_migrations + [the_migration])

    assert pristine_before_migration(
        adding, results_before_migration[0], the_column), (
            "Database inconsistent before applying migration.")
    assert applied_successfully(
        adding, results_after_migration[0], the_column), "Migration failed"

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "migration_file,the_table,the_column,adding", test_params)
def test_rollback_add_remove_column(
        auth_migrations_dir, auth_testdb_path, backend, migration_file,
        the_table, the_column, adding):
    """
    GIVEN: A migration that alters a table, adding or removing a column
    WHEN: The migration is applied
    THEN: Ensure the column is dropped if `adding` is True, otherwise, ensure
          the column has been restored
    """
    migration_path = f"{auth_migrations_dir}/{migration_file}"
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    the_migration = get_migration(migration_path)
    apply_migrations(backend, older_migrations)
    apply_single_migration(backend, the_migration)
    with closing(sqlite3.connect(auth_testdb_path)) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(query, (the_table,))
        results_before_migration = cursor.fetchone()
        rollback_single_migration(backend, the_migration)
        cursor.execute(query, (the_table,))
        results_after_migration = cursor.fetchone()

    rollback_migrations(backend, older_migrations + [the_migration])

    assert pristine_before_migration(
        not adding, results_before_migration[0], the_column), (
            "Database inconsistent before applying migration.")
    assert applied_successfully(
        not adding, results_after_migration[0], the_column), "Migration failed"
