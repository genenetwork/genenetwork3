"""Test migrations that create tables"""
import pytest

from gn3.auth import db
from gn3.migrations import get_migration, apply_migrations, rollback_migrations
from tests.unit.auth.conftest import (
    apply_single_migration, rollback_single_migration, migrations_up_to)

migrations_and_tables = (
    ("20221103_01_js9ub-initialise-the-auth-entic-oris-ation-database.py",
     "users"),
    ("20221103_02_sGrIs-create-user-credentials-table.py", "user_credentials"),
    ("20221108_01_CoxYh-create-the-groups-table.py", "groups"),
    ("20221108_02_wxTr9-create-privileges-table.py", "privileges"),
    ("20221108_03_Pbhb1-create-resource-categories-table.py", "resource_categories"),
    ("20221110_01_WtZ1I-create-resources-table.py", "resources"),
    ("20221110_05_BaNtL-create-roles-table.py", "roles"),
    ("20221110_06_Pq2kT-create-generic-roles-table.py", "generic_roles"),
    ("20221110_07_7WGa1-create-role-privileges-table.py", "role_privileges"),
    ("20221114_01_n8gsF-create-generic-role-privileges-table.py",
     "generic_role_privileges"),
    ("20221114_03_PtWjc-create-group-roles-table.py", "group_roles"),
    ("20221114_05_hQun6-create-user-roles-table.py", "user_roles"),
    ("20221117_02_fmuZh-create-group-users-table.py", "group_users"),
    ("20221206_01_BbeF9-create-group-user-roles-on-resources-table.py",
     "group_user_roles_on_resources"),
    ("20221219_01_CI3tN-create-oauth2-clients-table.py", "oauth2_clients"),
    ("20221219_02_buSEU-create-oauth2-tokens-table.py", "oauth2_tokens"),
    ("20221219_03_PcTrb-create-authorisation-code-table.py",
     "authorisation_code"),
    ("20230207_01_r0bkZ-create-group-join-requests-table.py",
     "group_join_requests"),
    ("20230322_01_0dDZR-create-linked-phenotype-data-table.py",
     "linked_phenotype_data"),
    ("20230322_02_Ll854-create-phenotype-resources-table.py",
     "phenotype_resources"),
    ("20230404_01_VKxXg-create-linked-genotype-data-table.py",
     "linked_genotype_data"),
    ("20230404_02_la33P-create-genotype-resources-table.py",
     "genotype_resources"),
    ("20230410_01_8mwaf-create-linked-mrna-data-table.py", "linked_mrna_data"),
    ("20230410_02_WZqSf-create-mrna-resources-table.py", "mrna_resources"))

@pytest.mark.unit_test
@pytest.mark.parametrize("migration_file,the_table", migrations_and_tables)
def test_create_table(
        auth_testdb_path, auth_migrations_dir, backend, migration_file,
        the_table):
    """
    GIVEN: A database migration script to create table, `the_table`
    WHEN: The migration is applied
    THEN: Ensure that the table `the_table` is created
    """
    migration_path=f"{auth_migrations_dir}/{migration_file}"
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    apply_migrations(backend, older_migrations)
    with db.connection(auth_testdb_path) as conn, db.cursor(conn) as cursor:
        cursor.execute("SELECT name FROM sqlite_schema WHERE type='table'")
        result_before_migration = cursor.fetchall()
        apply_single_migration(backend, get_migration(migration_path))
        cursor.execute("SELECT name FROM sqlite_schema WHERE type='table'")
        result_after_migration = cursor.fetchall()

    rollback_migrations(backend, older_migrations)
    assert the_table not in [row[0] for row in result_before_migration]
    assert the_table in [row[0] for row in result_after_migration]

@pytest.mark.unit_test
@pytest.mark.parametrize("migration_file,the_table", migrations_and_tables)
def test_rollback_create_table(
        auth_testdb_path, auth_migrations_dir, backend, migration_file,
        the_table):
    """
    GIVEN: A database migration script to create the table `the_table`
    WHEN: The migration is rolled back
    THEN: Ensure that the table `the_table` no longer exists
    """
    migration_path=f"{auth_migrations_dir}/{migration_file}"
    older_migrations = migrations_up_to(migration_path, auth_migrations_dir)
    apply_migrations(backend, older_migrations)
    with db.connection(auth_testdb_path) as conn, db.cursor(conn) as cursor:
        apply_single_migration(backend, get_migration(migration_path))
        cursor.execute("SELECT name FROM sqlite_schema WHERE type='table'")
        result_after_migration = cursor.fetchall()
        rollback_single_migration(backend, get_migration(migration_path))
        cursor.execute("SELECT name FROM sqlite_schema WHERE type='table'")
        result_after_rollback = cursor.fetchall()

    rollback_migrations(backend, older_migrations)
    assert the_table in [row[0] for row in result_after_migration]
    assert the_table not in [row[0] for row in result_after_rollback]
