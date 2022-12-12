"""Fixtures and utilities for role-related tests"""
import pytest

from gn3.auth import db

@pytest.fixture(scope="function")
def fixture_user_roles(test_users_in_group):
    conn, *_others = test_users_in_group
    raise Exception("NOT IMPLEMENTED ...")
