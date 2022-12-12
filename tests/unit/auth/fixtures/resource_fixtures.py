"""Fixtures and utilities for resource-related tests"""
import uuid

import pytest

from gn3.auth import db
from gn3.auth.authorisation.resources import Resource, ResourceCategory

from .group_fixtures import TEST_GROUPS

TEST_RESOURCES = (
    Resource(TEST_GROUPS[0], uuid.UUID("26ad1668-29f5-439d-b905-84d551f85955"),
             "ResourceG01R01",
             ResourceCategory(uuid.UUID("48056f84-a2a6-41ac-8319-0e1e212cba2a"),
                              "genotype", "Genotype Dataset"),
             True),
    Resource(TEST_GROUPS[0], uuid.UUID("2130aec0-fefd-434d-92fd-9ca342348b2d"),
             "ResourceG01R02",
             ResourceCategory(uuid.UUID("548d684b-d4d1-46fb-a6d3-51a56b7da1b3"),
                              "phenotype", "Phenotype (Publish) Dataset"),
             False),
    Resource(TEST_GROUPS[0], uuid.UUID("e9a1184a-e8b4-49fb-b713-8d9cbeea5b83"),
             "ResourceG01R03",
             ResourceCategory(uuid.UUID("fad071a3-2fc8-40b8-992b-cdefe7dcac79"),
                              "mrna", "mRNA Dataset"),
             False),
    Resource(TEST_GROUPS[1], uuid.UUID("14496a1c-c234-49a2-978c-8859ea274054"),
             "ResourceG02R01",
             ResourceCategory(uuid.UUID("48056f84-a2a6-41ac-8319-0e1e212cba2a"),
                              "genotype", "Genotype Dataset"),
             False),
    Resource(TEST_GROUPS[1], uuid.UUID("04ad9e09-94ea-4390-8a02-11f92999806b"),
             "ResourceG02R02",
             ResourceCategory(uuid.UUID("fad071a3-2fc8-40b8-992b-cdefe7dcac79"),
                              "mrna", "mRNA Dataset"),
             True))

@pytest.fixture(scope="function")
def test_resources(test_group):# pylint: disable=[redefined-outer-name]
    """fixture: setup test resources in the database"""
    conn, _group = test_group
    with db.cursor(conn) as cursor:
        cursor.executemany(
            "INSERT INTO resources VALUES (?,?,?,?,?)",
        ((str(res.group.group_id), str(res.resource_id), res.resource_name,
          str(res.resource_category.resource_category_id),
          1 if res.public else 0) for res in TEST_RESOURCES))
    return (conn, TEST_RESOURCES)

@pytest.fixture(scope="function")
def fixture_user_resources(test_users_in_group, test_resources):# pylint: disable=[redefined-outer-name, unused-argument]
    """fixture: link users to roles and resources"""
    conn, _resources = test_resources
    ## TODO: setup user roles
    ## TODO: attach user roles to specific resources
    return conn
