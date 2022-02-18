"""Test partial correlations"""
import pytest

from tests.integration.conftest import client

@pytest.mark.integration_test
@pytest.mark.parametrize(
    "post_data", (
        None, {}, {
            "primary_trait": None,
            "control_traits": None,
            "method": None,
            "target_db": None
        }, {
            "primary_trait": None,
            "control_traits": None,
            "method": None,
            "target_db": "a_db"
        }, {
            "primary_trait": None,
            "control_traits": None,
            "method": "a_method",
            "target_db": None
        }, {
            "primary_trait": None,
            "control_traits": None,
            "method": "a_method",
            "target_db": "a_db"
        }, {
            "primary_trait": None,
            "control_traits": ["a_trait", "another"],
            "method": None,
            "target_db": None
        }, {
            "primary_trait": None,
            "control_traits": ["a_trait", "another"],
            "method": None,
            "target_db": "a_db"
        }, {
            "primary_trait": None,
            "control_traits": ["a_trait", "another"],
            "method": "a_method",
            "target_db": None
        }, {
            "primary_trait": None,
            "control_traits": ["a_trait", "another"],
            "method": "a_method",
            "target_db": "a_db"
        }, {
            "primary_trait": "a_trait",
            "control_traits": None,
            "method": None,
            "target_db": None
        }, {
            "primary_trait": "a_trait",
            "control_traits": None,
            "method": None,
            "target_db": "a_db"
        }, {
            "primary_trait": "a_trait",
            "control_traits": None,
            "method": "a_method",
            "target_db": None
        }, {
            "primary_trait": "a_trait",
            "control_traits": None,
            "method": "a_method",
            "target_db": "a_db"
        }, {
            "primary_trait": "a_trait",
            "control_traits": ["a_trait", "another"],
            "method": None,
            "target_db": None
        }, {
            "primary_trait": "a_trait",
            "control_traits": ["a_trait", "another"],
            "method": None,
            "target_db": "a_db"
        }, {
            "primary_trait": "a_trait",
            "control_traits": ["a_trait", "another"],
            "method": "a_method",
            "target_db": None
        }))
def test_partial_correlation_api_with_missing_request_data(client, post_data):
    """
    Test /api/correlations/partial endpoint with various expected request data
    missing.
    """
    response = client.post("/api/correlation/partial", json=post_data)
    assert (
        response.status_code == 400 and response.is_json and
        response.json.get("status") == "error")


@pytest.mark.integration_test
@pytest.mark.slow
@pytest.mark.parametrize(
    "post_data",
    ({# ProbeSet
        "primary_trait": {"dataset": "a_dataset", "name": "a_name"},
        "control_traits": [
            {"dataset": "a_dataset", "name": "a_name"},
            {"dataset": "a_dataset2", "name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }, {# Publish
        "primary_trait": {"dataset": "a_Publish_dataset", "name": "a_name"},
        "control_traits": [
            {"dataset": "a_dataset", "name": "a_name"},
            {"dataset": "a_dataset2", "name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }, {# Geno
        "primary_trait": {"dataset": "a_Geno_dataset", "name": "a_name"},
        "control_traits": [
            {"dataset": "a_dataset", "name": "a_name"},
            {"dataset": "a_dataset2", "name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }, {# Temp -- Fails due to missing table. Remove this sample if it is
        # confirmed that the deletion of the database table is on purpose, and
        # that Temp traits are no longer a thing
        "primary_trait": {"dataset": "a_Temp_dataset", "name": "a_name"},
        "control_traits": [
            {"dataset": "a_dataset", "name": "a_name"},
            {"dataset": "a_dataset2", "name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }))
def test_partial_correlation_api_with_non_existent_traits(client, post_data):
    """
    Check that the system responds appropriately in the case where the user
    makes a request with a non-existent primary trait.
    """
    response = client.post("/api/correlation/partial", json=post_data)
    assert (
        response.status_code == 404 and response.is_json and
        response.json.get("status") != "error")
