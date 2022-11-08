"""Test the auth database initialisation migration."""
from contextlib import closing

import pytest
import sqlite3

from gn3.migrations import get_migration, apply_migrations, rollback_migrations
from tests.unit.auth.conftest import (
    apply_single_migration, rollback_single_migration, migrations_up_to)

migration_path = "migrations/auth/20221103_02_sGrIs-create-user-credentials-table.py"

@pytest.mark.unit_test
def test_create_user_credentials_table(auth_testdb_path, backend, all_migrations):
    """
    GIVEN: A database migration script to create the `user_credentials` table
    WHEN: The migration is applied
    THEN: Ensure that the table is created
    """
    older_migrations = migrations_up_to(migration_path, "migrations/auth/")
    apply_migrations(backend, older_migrations)
    with closing(sqlite3.connect(auth_testdb_path)) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT name FROM sqlite_schema WHERE type='table'")
        result = cursor.fetchall()
        assert "users_credentials" not in [row[0] for row in cursor.fetchall()]
        apply_single_migration(auth_testdb_path, get_migration(migration_path))
        cursor.execute("SELECT name FROM sqlite_schema WHERE type='table'")
        assert "user_credentials" in [row[0] for row in cursor.fetchall()]

    rollback_migrations(backend, older_migrations)

@pytest.mark.unit_test
def test_rollback_create_user_credentials_table(auth_testdb_path, backend):
    """
    GIVEN: A database migration script to create the `user_credentials` table
    WHEN: The migration is rolled back
    THEN: Ensure that the `user_credentials` table no longer exists
    """
    older_migrations = migrations_up_to(migration_path, "migrations/auth/")
    apply_migrations(backend, older_migrations)
    with closing(sqlite3.connect(auth_testdb_path)) as conn, closing(conn.cursor()) as cursor:
        apply_single_migration(auth_testdb_path, get_migration(migration_path))
        rollback_single_migration(auth_testdb_path, get_migration(migration_path))
        cursor.execute("SELECT name FROM sqlite_schema WHERE type='table'")
        assert "user_credentials" not in [row[0] for row in cursor.fetchall()]

    rollback_migrations(backend, older_migrations)
