"""Tests for the LMDB sample data API endpoint"""
import pytest


@pytest.mark.unit_test
def test_nonexistent_data(client):
    """Test endpoint returns 404 when data doesn't exist"""
    response = client.get("/api/lmdb/sample-data/nonexistent/123")
    assert response.status_code == 404
    assert response.json["error"] == "No data found for given dataset and trait"


@pytest.mark.unit_test
def test_successful_retrieval(client):
    """Test successful data retrieval using test LMDB data"""
    # Use known test data hash: 7308efbd84b33ad3d69d14b5b1f19ccc
    response = client.get("/api/lmdb/sample-data/BXDPublish/10007")
    assert response.status_code == 200

    data = response.json
    assert len(data) == 31
    # Verify some known values from the test database
    assert data["BXD1"] == 18.700001
    assert data["BXD11"] == 18.9


@pytest.mark.unit_test
def test_invalid_trait_id(client):
    """Test endpoint handles invalid trait IDs appropriately"""
    response = client.get("/api/lmdb/sample-data/BXDPublish/999999")
    assert response.status_code == 404
