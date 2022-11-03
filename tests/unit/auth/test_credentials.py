"""Test the credentials checks"""
import sqlite3

import pytest
from contextlib import closing
from hypothesis import given, settings, strategies, HealthCheck

from gn3.auth.authentication import credentials_in_database

@pytest.mark.unit_test
@given(strategies.emails(), strategies.text())
@settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
def test_credentials_not_in_database(conn_after_auth_migrations, email, password):
    """
    GIVEN: credentials that do not exist in the database
    WHEN: the `credentials_in_database` function is run against the credentials
    THEN: check that the function returns false in all cases.
    """
    with closing(conn_after_auth_migrations.cursor()) as cursor:
        results = credentials_in_database(cursor, email, password)
        assert credentials_in_database(cursor, email, password) is False
