"""Test fixtures to set up a test named graph for loading RDF data."""
import os

import pytest
import requests
from requests.auth import HTTPDigestAuth


def get_sparql_auth_conf(config_obj) -> dict:
    """Fetch SPARQL auth configuration from the configuration object."""
    return {
        "sparql_user": config_obj["SPARQL_USER"],
        "sparql_auth_uri": config_obj["SPARQL_AUTH_URI"],
        "sparql_crud_auth_uri": config_obj["SPARQL_CRUD_AUTH_URI"],
        "sparql_endpoint": config_obj["SPARQL_ENDPOINT"],
        "sparql_password": config_obj["SPARQL_PASSWORD"],
    }


# XXXX: Currently we run the tests against CD's virtuoso instance.
# This is not idempotent.  Consider having a special virtuoso instance
# just for running tests.
@pytest.fixture(scope="module")
def rdf_setup(fxtr_app_config):
    """Upload RDF to a Virtuoso named graph"""
    # Define the URL and file
    sparql_conf = get_sparql_auth_conf(fxtr_app_config)
    url = sparql_conf["sparql_crud_auth_uri"]
    file_path = os.path.join(
        os.path.dirname(__file__).split("fixtures")[0],
        "test_data/ttl-files/test-data.ttl",
    )

    # Define the query parameters and authentication
    params = {"graph": "http://cd-test.genenetwork.org"}
    auth = HTTPDigestAuth(
        sparql_conf["sparql_user"], sparql_conf["sparql_password"])

    # Make sure this graph does not exist before running anything
    requests.delete(url, params=params, auth=auth)

    # Open the file in binary mode and send the request
    with open(file_path, "rb") as file:
        response = requests.put(url, params=params, auth=auth, data=file)
    yield response
    requests.delete(url, params=params, auth=auth)
