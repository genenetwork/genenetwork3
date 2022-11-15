"""Test migrations that create tables"""

import pytest

from gn3.auth import db
from gn3.migrations import get_migration, apply_migrations, rollback_migrations
from tests.unit.auth.conftest import (
    apply_single_migration, rollback_single_migration, migrations_up_to)

test_params = (
    ("20221114_02_DKKjn-drop-generic-role-tables.py", "generic_roles"),
    ("20221114_02_DKKjn-drop-generic-role-tables.py", "generic_role_privileges"))

@pytest.mark.unit_test
@pytest.mark.parametrize("migration_file,the_table", test_params)
def test_drop_table(
        auth_testdb_path, auth_migrations_dir, backend,
        migration_file, the_table):
    """
    GIVEN: A database migration script to create table, `the_table`
    WHEN: The migration is applied
    THEN: Ensure that the table `the_table` is created
    """
    migration_path=f"{auth_migrations_dir}/{migration_file}"
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    the_migration = get_migration(migration_path)
    apply_migrations(backend, older_migrations)
    with db.connection(auth_testdb_path) as conn, db.cursor(conn) as cursor:
        cursor.execute("SELECT name FROM sqlite_schema WHERE type='table'")
        result_before_migration = cursor.fetchall()
        apply_single_migration(backend, the_migration)
        cursor.execute("SELECT name FROM sqlite_schema WHERE type='table'")
        result_after_migration = cursor.fetchall()

    rollback_migrations(backend, older_migrations + [the_migration])
    assert the_table in [row[0] for row in result_before_migration]
    assert the_table not in [row[0] for row in result_after_migration]

@pytest.mark.unit_test
@pytest.mark.parametrize("migration_file,the_table", test_params)
def test_rollback_drop_table(
        auth_testdb_path, auth_migrations_dir, backend, migration_file,
        the_table):
    """
    GIVEN: A database migration script to create the table `the_table`
    WHEN: The migration is rolled back
    THEN: Ensure that the table `the_table` no longer exists
    """
    migration_path=f"{auth_migrations_dir}/{migration_file}"
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    the_migration = get_migration(migration_path)
    apply_migrations(backend, older_migrations)
    with db.connection(auth_testdb_path) as conn, db.cursor(conn) as cursor:
        apply_single_migration(backend, the_migration)
        cursor.execute("SELECT name FROM sqlite_schema WHERE type='table'")
        result_after_migration = cursor.fetchall()
        rollback_single_migration(backend, the_migration)
        cursor.execute("SELECT name FROM sqlite_schema WHERE type='table'")
        result_after_rollback = cursor.fetchall()

    rollback_migrations(backend, older_migrations)
    assert the_table not in [row[0] for row in result_after_migration]
    assert the_table in [row[0] for row in result_after_rollback]
