"""Test migration adding the `resource_meta` field to `resource_categories` table."""
from contextlib import closing

import pytest
import sqlite3

from gn3.migrations import get_migration, apply_migrations, rollback_migrations
from tests.unit.auth.conftest import (
    migrations_up_to, apply_single_migration, rollback_single_migration)

migration_path = "migrations/auth/20221109_01_HbD5F-add-resource-meta-field-to-resource-categories-field.py"

def __has_resource_meta(value: str):
    return value.find("resource_meta TEXT") >= 0

@pytest.mark.unit_test
def test_apply_add_resource_meta(auth_migrations_dir, auth_testdb_path, backend):
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    the_migration = get_migration(migration_path)
    apply_migrations(backend, older_migrations)
    with closing(sqlite3.connect(auth_testdb_path)) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            "SELECT sql FROM sqlite_schema WHERE name=?",
            ("resource_categories",))
        results_before_migration = cursor.fetchone()
        apply_single_migration(backend, the_migration)
        cursor.execute(
            "SELECT sql FROM sqlite_schema WHERE name=?",
            ("resource_categories",))
        results_after_migration = cursor.fetchone()

    rollback_migrations(backend, older_migrations + [the_migration])

    assert not any(
        [__has_resource_meta(line.strip())
         for line in results_before_migration[0].split("\n")]
    ), "`resource_meta` field exists in table before migration."
    assert any(
        [__has_resource_meta(line.strip())
         for line in results_after_migration[0].split("\n")]
    ), "Couldn't find `resource_meta` field in table"

@pytest.mark.unit_test
def test_rollback_add_resource_meta(auth_migrations_dir, auth_testdb_path, backend):
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    the_migration = get_migration(migration_path)
    apply_migrations(backend, older_migrations)
    with closing(sqlite3.connect(auth_testdb_path)) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            "SELECT sql FROM sqlite_schema WHERE name=?",
            ("resource_categories",))
        results_before_migration = cursor.fetchone()
        apply_single_migration(backend, the_migration)
        cursor.execute(
            "SELECT sql FROM sqlite_schema WHERE name=?",
            ("resource_categories",))
        results_after_migration = cursor.fetchone()
        rollback_single_migration(backend, the_migration)
        cursor.execute(
            "SELECT sql FROM sqlite_schema WHERE name=?",
            ("resource_categories",))
        results_after_rollback = cursor.fetchone()

    rollback_migrations(backend, older_migrations)

    assert not any ([
        __has_resource_meta(line.strip())
        for line in results_before_migration[0].split("\n")]
    ), "`resource_meta` field exists in table before migration."
    assert any([
        __has_resource_meta(line.strip())
        for line in results_after_migration[0].split("\n")]
    ), "Couldn't find `resource_meta` field in table"
    assert not any([
        __has_resource_meta(line.strip())
        for line in results_after_rollback[0].split("\n")]
    ), "`resource_meta` field exists in table after rollback."
