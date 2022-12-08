"""Test migrations that alter tables adding/removing columns."""
import pytest

from gn3.auth import db
from gn3.migrations import get_migration, apply_migrations, rollback_migrations
from tests.unit.auth.conftest import (
    apply_single_migration, rollback_single_migration, migrations_up_to)

QUERY = "SELECT sql FROM sqlite_schema WHERE name=?"

TEST_PARAMS = (
    ("20221109_01_HbD5F-add-resource-meta-field-to-resource-categories-field.py",
     "resource_categories", "resource_meta TEXT", True),
    (("20221110_08_23psB-add-privilege-category-and-privilege-description-"
      "columns-to-privileges-table.py"),
     "privileges", "privilege_category TEXT", True),
    (("20221110_08_23psB-add-privilege-category-and-privilege-description-"
      "columns-to-privileges-table.py"),
     "privileges", "privilege_description TEXT", True),
    ("20221117_01_RDlfx-modify-group-roles-add-group-role-id.py", "group_roles",
     "group_role_id", True),
    ("20221208_01_sSdHz-add-public-column-to-resources-table.py", "resources",
     "public", True))

def found(haystack: str, needle: str) -> bool:
    """Check whether `needle` is found in `haystack`"""
    return any(
        (line.strip().find(needle) >= 0) for line in haystack.split("\n"))

def pristine_before_migration(adding: bool, result_str: str, column: str) -> bool:
    """Check that database is pristine before running the migration"""
    col_was_found = found(result_str, column)
    if adding:
        return not col_was_found
    return col_was_found

def applied_successfully(adding: bool, result_str: str, column: str) -> bool:
    """Check that the migration ran successfully"""
    col_was_found = found(result_str, column)
    if adding:
        return col_was_found
    return not col_was_found

def rolled_back_successfully(adding: bool, result_str: str, column: str) -> bool:
    """Check that the migration ran successfully"""
    col_was_found = found(result_str, column)
    if adding:
        return not col_was_found
    return col_was_found

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "migration_file,the_table,the_column,adding", TEST_PARAMS)
def test_apply_add_remove_column(# pylint: disable=[too-many-arguments]
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
    with db.connection(auth_testdb_path) as conn, db.cursor(conn) as cursor:
        cursor.execute(QUERY, (the_table,))
        results_before_migration = cursor.fetchone()
        apply_single_migration(backend, the_migration)
        cursor.execute(QUERY, (the_table,))
        results_after_migration = cursor.fetchone()

    rollback_migrations(backend, older_migrations + [the_migration])

    assert pristine_before_migration(
        adding, results_before_migration[0], the_column), (
            f"Column `{the_column}` exists before migration and should not"
            if adding else
            f"Column `{the_column}` doesn't exist before migration and it should")
    assert applied_successfully(
        adding, results_after_migration[0], the_column), "Migration failed"

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "migration_file,the_table,the_column,adding", TEST_PARAMS)
def test_rollback_add_remove_column(# pylint: disable=[too-many-arguments]
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
    with db.connection(auth_testdb_path) as conn, db.cursor(conn) as cursor:
        cursor.execute(QUERY, (the_table,))
        results_before_rollback = cursor.fetchone()
        rollback_single_migration(backend, the_migration)
        cursor.execute(QUERY, (the_table,))
        results_after_rollback = cursor.fetchone()

    rollback_migrations(backend, older_migrations + [the_migration])

    assert pristine_before_migration(
        not adding, results_before_rollback[0], the_column), (
            f"Column `{the_column}` doesn't exist before rollback and it should"
            if adding else
            f"Column `{the_column}` exists before rollback and should not")
    assert rolled_back_successfully(
        adding, results_after_rollback[0], the_column), "Rollback failed"
