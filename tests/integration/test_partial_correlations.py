"""Test partial correlations"""
from unittest import mock

import pytest

from gn3.computations.partial_correlations import partial_correlations_entry

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
        "primary_trait": {"dataset": "a_dataset", "trait_name": "a_name"},
        "control_traits": [
            {"dataset": "a_dataset", "trait_name": "a_name"},
            {"dataset": "a_dataset2", "trait_name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }, {# Publish
        "primary_trait": {
            "dataset": "a_Publish_dataset", "trait_name": "a_name"},
        "control_traits": [
            {"dataset": "a_dataset", "trait_name": "a_name"},
            {"dataset": "a_dataset2", "trait_name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }, {# Geno
        "primary_trait": {"dataset": "a_Geno_dataset", "trait_name": "a_name"},
        "control_traits": [
            {"dataset": "a_dataset", "trait_name": "a_name"},
            {"dataset": "a_dataset2", "trait_name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }, {# Temp
        "primary_trait": {"dataset": "a_Temp_dataset", "trait_name": "a_name"},
        "control_traits": [
            {"dataset": "a_dataset", "trait_name": "a_name"},
            {"dataset": "a_dataset2", "trait_name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }))
def test_partial_correlation_api_with_non_existent_primary_traits(
        client, post_data, mocker):
    """
    Check that the system responds appropriately in the case where the user
    makes a request with a non-existent primary trait.
    """
    mocker.patch("gn3.api.correlation.redis.Redis", mock.MagicMock())
    response = client.post("/api/correlation/partial", json=post_data)
    assert (
        response.status_code == 200 and response.is_json and
        response.json.get("status") == "success")

@pytest.mark.integration_test
@pytest.mark.slow
@pytest.mark.parametrize(
    "post_data",
    ({# ProbeSet
        "primary_trait": {
            "dataset": "UCLA_BXDBXH_CARTILAGE_V2",
            "trait_name": "ILM103710672"},
        "control_traits": [
            {"dataset": "a_dataset", "trait_name": "a_name"},
            {"dataset": "a_dataset2", "trait_name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }, {# Publish
        "primary_trait": {"dataset": "BXDPublish", "trait_name": "BXD_12557"},
        "control_traits": [
            {"dataset": "a_dataset", "trait_name": "a_name"},
            {"dataset": "a_dataset2", "trait_name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }, {# Geno
        "primary_trait": {"dataset": "AKXDGeno", "trait_name": "D4Mit16"},
        "control_traits": [
            {"dataset": "a_dataset", "trait_name": "a_name"},
            {"dataset": "a_dataset2", "trait_name": "a_name2"}],
        "method": "a_method",
        "target_db": "a_db"
    }
     # Temp -- the data in the database for these is ephemeral, making it
     #         difficult to test for this
     ))
def test_partial_correlation_api_with_non_existent_control_traits(client, post_data, mocker):
    """
    Check that the system responds appropriately in the case where the user
    makes a request with a non-existent control traits.

    The code repetition here is on purpose - valuing clarity over succinctness.
    """
    mocker.patch("gn3.api.correlation.redis.Redis", mock.MagicMock())
    response = client.post("/api/correlation/partial", json=post_data)
    assert (
        response.status_code == 200 and response.is_json and
        response.json.get("status") == "success")

@pytest.mark.integration_test
@pytest.mark.slow
@pytest.mark.parametrize(
    "primary,controls,method,target", (
        (# Probeset
            "UCLA_BXDBXH_CARTILAGE_V2::ILM103710672", (
                "UCLA_BXDBXH_CARTILAGE_V2::nonExisting01",
                "UCLA_BXDBXH_CARTILAGE_V2::nonExisting02",
                "UCLA_BXDBXH_CARTILAGE_V2::ILM380019"),
            "Genetic Correlation, Pearson's r", "BXDPublish"),
        (# Publish
            "BXDPublish::17937", (
                "BXDPublish::17940",
                "BXDPublish::nonExisting03"),
            "Genetic Correlation, Spearman's rho", "BXDPublish"),
        (# Geno
            "AKXDGeno::D4Mit16", (
                "AKXDGeno::D1Mit170",
                "AKXDGeno::nonExisting04",
                "AKXDGeno::D1Mit135",
                "AKXDGeno::nonExisting05",
                "AKXDGeno::nonExisting06"),
            "SGO Literature Correlation", "BXDPublish")
    )
    # Temp -- the data in the database for these is ephemeral, making it
    #         difficult to test for these without a temp database with the temp
    #         traits data set to something we are in control of
     )

def test_part_corr_api_with_mix_of_existing_and_non_existing_control_traits(
        db_conn, primary, controls, method, target):
    """
    Check that calling the function with a mix of existing and missing control
    traits raises an warning.
    """
    criteria = 10
    with pytest.warns(UserWarning):
        partial_correlations_entry(
            db_conn, primary, controls, method, criteria, target)
