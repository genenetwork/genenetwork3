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
    "Test /api/correlations/partial"
    response = client.post("/api/correlation/partial", json=post_data)
    assert (
        response.status_code == 400 and response.is_json and
        response.json.get("status") == "error")
