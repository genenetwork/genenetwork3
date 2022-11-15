"""Test the credentials checks"""
import pytest
from yoyo.migrations import MigrationList
from hypothesis import given, settings, strategies, HealthCheck

from gn3.auth import db
from gn3.auth.authentication import credentials_in_database
from gn3.migrations import get_migration, apply_migrations, rollback_migrations

from tests.unit.auth.conftest import migrations_up_to

@pytest.fixture
def with_credentials_table(backend, auth_testdb_path):
    """
    Fixture: Yield a connection object with the 'user_credentials' table
    created.
    """
    migrations_dir = "migrations/auth"
    migration = f"{migrations_dir}/20221103_02_sGrIs-create-user-credentials-table.py"
    migrations = (migrations_up_to(migration, migrations_dir) +
                  MigrationList([get_migration(migration)]))
    apply_migrations(backend, migrations)
    with db.connection(auth_testdb_path) as conn:
        yield conn

    rollback_migrations(backend, migrations)

@pytest.fixture
def with_credentials(with_credentials_table):# pylint: disable=redefined-outer-name
    """
    Fixture: Initialise the database with some user credentials.
    """
    with db.cursor(with_credentials_table) as cursor:
        cursor.executemany(
            "INSERT INTO users VALUES (:user_id, :email, :name)",
            ({"user_id": "82552014-21ee-4321-b96a-b8788b97b862",
              "email": "first@test.user",
              "name": "First Test User"
              },
             {"user_id": "bdd5cb7a-072d-4c2b-9872-d0cecb718523",
              "email": "second@test.user",
              "name": "Second Test User"
              }))
        cursor.executemany(
            "INSERT INTO user_credentials VALUES (:user_id, :password)",
            ({"user_id": "82552014-21ee-4321-b96a-b8788b97b862",
              "password": b'$2b$12$LAh1PYtUgAFK7d5fA0EfL.4AdTZuYEAfzwO.p.jXVboxcP8bXNj7a'
              },
             {"user_id": "bdd5cb7a-072d-4c2b-9872-d0cecb718523",
              "password": b'$2b$12$zX77QCFSJuwIjAZGc0Jq5.rCWMHEMKD9Zf3Ay4C0AzwsiZ7SSPdKO'
              }))

        yield with_credentials_table

        cursor.executemany("DELETE FROM user_credentials WHERE user_id=?",
                           (("82552014-21ee-4321-b96a-b8788b97b862",),
                            ("bdd5cb7a-072d-4c2b-9872-d0cecb718523",)))
        cursor.executemany("DELETE FROM users WHERE user_id=?",
                           (("82552014-21ee-4321-b96a-b8788b97b862",),
                            ("bdd5cb7a-072d-4c2b-9872-d0cecb718523",)))

@pytest.mark.unit_test
@given(strategies.emails(), strategies.text())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_credentials_not_in_database(with_credentials, email, password):# pylint: disable=redefined-outer-name
    """
    GIVEN: credentials that do not exist in the database
    WHEN: the `credentials_in_database` function is run against the credentials
    THEN: check that the function returns false in all cases.
    """
    with db.cursor(with_credentials) as cursor:
        assert credentials_in_database(cursor, email, password) is False

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "email,password",
    (("first@test.user", "wrongpassword"),
     ("first@tes.user", "testuser01")))
def test_partially_wrong_credentials(with_credentials, email, password):# pylint: disable=redefined-outer-name
    """
    GIVEN: credentials that exist in the database
    WHEN: the credentials are checked with partially wrong values
    THEN: the check fails since the credentials are not correct
    """
    with db.cursor(with_credentials) as cursor:
        assert credentials_in_database(cursor, email, password) is False

@pytest.mark.unit_test
@pytest.mark.parametrize(
    "email,password",
    (("first@test.user", "testuser01"),
     ("second@test.user", "testuser02")))
def test_partially_correct_credentials(with_credentials, email, password):# pylint: disable=redefined-outer-name
    """
    GIVEN: credentials that exist in the database
    WHEN: the credentials are checked with correct values
    THEN: the check passes
    """
    with db.cursor(with_credentials) as cursor:
        assert credentials_in_database(cursor, email, password) is True
