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
    }, {# Temp
        "primary_trait": {"dataset": "a_Temp_dataset", "name": "a_name"},
        "control_traits": [
            {"dataset": "a_dataset", "name": "a_name"},
            {"dataset": "a_dataset2", "name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }))
def test_partial_correlation_api_with_non_existent_primary_traits(client, post_data):
    """
    Check that the system responds appropriately in the case where the user
    makes a request with a non-existent primary trait.
    """
    response = client.post("/api/correlation/partial", json=post_data)
    assert (
        response.status_code == 404 and response.is_json and
        response.json.get("status") != "error")

@pytest.mark.integration_test
@pytest.mark.slow
@pytest.mark.parametrize(
    "post_data",
    ({# ProbeSet
        "primary_trait": {
            "dataset": "UCLA_BXDBXH_CARTILAGE_V2", "name": "ILM103710672"},
        "control_traits": [
            {"dataset": "a_dataset", "name": "a_name"},
            {"dataset": "a_dataset2", "name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }, {# Publish
        "primary_trait": {"dataset": "BXDPublish", "name": "BXD_12557"},
        "control_traits": [
            {"dataset": "a_dataset", "name": "a_name"},
            {"dataset": "a_dataset2", "name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }, {# Geno
        "primary_trait": {"dataset": "AKXDGeno", "name": "D4Mit16"},
        "control_traits": [
            {"dataset": "a_dataset", "name": "a_name"},
            {"dataset": "a_dataset2", "name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }
     # Temp -- the data in the database for these is ephemeral, making it
     #         difficult to test for this
     ))
def test_partial_correlation_api_with_non_existent_control_traits(client, post_data):
    """
    Check that the system responds appropriately in the case where the user
    makes a request with a non-existent control traits.

    The code repetition here is on purpose - valuing clarity over succinctness.
    """
    response = client.post("/api/correlation/partial", json=post_data)
    assert (
        response.status_code == 404 and response.is_json and
        response.json.get("status") != "error")
