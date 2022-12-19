"""Test data insertion when migrations are run."""
import pytest

from gn3.auth import db
from gn3.migrations import get_migration, apply_migrations, rollback_migrations
from tests.unit.auth.conftest import (
    apply_single_migration, rollback_single_migration, migrations_up_to)

test_params = (
    ("20221116_01_nKUmX-add-privileges-to-group-leader-role.py",
     ("SELECT role_id, privilege_id FROM role_privileges "
      "WHERE role_id=? AND privilege_id IN (?, ?, ?, ?)"),
     ("a0e67630-d502-4b9f-b23f-6805d0f30e30",
      "221660b1-df05-4be1-b639-f010269dbda9",
      "7bcca363-cba9-4169-9e31-26bdc6179b28",
      "5103cc68-96f8-4ebb-83a4-a31692402c9b",
      "1c59eff5-9336-4ed2-a166-8f70d4cb012e"),
     (("a0e67630-d502-4b9f-b23f-6805d0f30e30",
       "221660b1-df05-4be1-b639-f010269dbda9"),
      ("a0e67630-d502-4b9f-b23f-6805d0f30e30",
       "7bcca363-cba9-4169-9e31-26bdc6179b28"),
      ("a0e67630-d502-4b9f-b23f-6805d0f30e30",
       "5103cc68-96f8-4ebb-83a4-a31692402c9b"),
      ("a0e67630-d502-4b9f-b23f-6805d0f30e30",
       "1c59eff5-9336-4ed2-a166-8f70d4cb012e"))),)

@pytest.mark.unit_test
@pytest.mark.parametrize("migration_file,query,query_params,data", test_params)
def test_apply_insert(# pylint: disable=[too-many-arguments]
        auth_migrations_dir, backend, auth_testdb_path, migration_file, query,
        query_params, data):
    """
    GIVEN: a database migration script
    WHEN: the script is applied
    THEN: ensure the given data exists in the table
    """
    migration_path=f"{auth_migrations_dir}/{migration_file}"
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    the_migration = get_migration(migration_path)
    apply_migrations(backend, older_migrations)
    with db.connection(auth_testdb_path, None) as conn, db.cursor(conn) as cursor:
        cursor.execute(query, query_params)
        result_before_migration = cursor.fetchall()
        apply_single_migration(backend, the_migration)
        cursor.execute(query, query_params)
        result_after_migration = cursor.fetchall()

    rollback_migrations(backend, older_migrations + [the_migration])
    assert len(result_before_migration) == 0, "Expected no results before migration"
    assert sorted(result_after_migration) == sorted(data)

@pytest.mark.unit_test
@pytest.mark.parametrize("migration_file,query,query_params,data", test_params)
def test_rollback_insert(# pylint: disable=[too-many-arguments]
        auth_migrations_dir, backend, auth_testdb_path, migration_file, query,
        query_params, data):
    """
    GIVEN: a database migration script
    WHEN: the script is rolled back
    THEN: ensure the given data no longer exists in the database
    """
    migration_path=f"{auth_migrations_dir}/{migration_file}"
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    the_migration = get_migration(migration_path)
    apply_migrations(backend, older_migrations)
    with db.connection(auth_testdb_path, None) as conn, db.cursor(conn) as cursor:
        cursor.execute(query, query_params)
        result_before_migration = cursor.fetchall()
        apply_single_migration(backend, the_migration)
        cursor.execute(query, query_params)
        result_after_migration = cursor.fetchall()
        rollback_single_migration(backend, the_migration)
        cursor.execute(query, query_params)
        result_after_rollback = cursor.fetchall()

    rollback_migrations(backend, older_migrations)
    assert len(result_before_migration) == 0, "Expected no results before migration"
    assert sorted(result_after_migration) == sorted(data)
    assert len(result_after_rollback) == 0, "Expected no results after rollback"
