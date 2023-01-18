"""Fixtures and utilities for resource-related tests"""
import pytest

from gn3.auth import db

from .group_fixtures import TEST_RESOURCES

@pytest.fixture(scope="function")
def fxtr_resources(fxtr_group):# pylint: disable=[redefined-outer-name]
    """fixture: setup test resources in the database"""
    conn, _group = fxtr_group
    with db.cursor(conn) as cursor:
        cursor.executemany(
            "INSERT INTO resources VALUES (?,?,?,?,?)",
        ((str(res.group.group_id), str(res.resource_id), res.resource_name,
          str(res.resource_category.resource_category_id),
          1 if res.public else 0) for res in TEST_RESOURCES))

    yield (conn, TEST_RESOURCES)

    with db.cursor(conn) as cursor:
        cursor.executemany(
            "DELETE FROM resources WHERE group_id=? AND resource_id=?",
        ((str(res.group.group_id), str(res.resource_id),)
         for res in TEST_RESOURCES))
