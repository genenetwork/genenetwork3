"""Test fixtures to set up a test named graph for loading RDF data."""
import os
from flask import config

import pytest
import requests
from requests.auth import HTTPDigestAuth


def get_sparql_auth_conf() -> dict:
    """Fetch SPARQL auth configuration from the configurafrom flask
    import configuration object."""
    # When loading from the environment, GN3_CONF precedes
    # GN3_SECRETS.  Don't change this order.
    sparql_conf = config.Config("")
    if os.environ.get("GN3_CONF"):
        # Check whether GN3_CONF has been set, and ignore GN3_CONF
        # otherwise.  In CD, we use a mixed-text file, so we don't
        # have an explicit PATH to point this to.
        # https://git.genenetwork.org/gn-machines/tree/genenetwork-development.scm#n517
        sparql_conf.from_envvar("GN3_CONF")
    # Set sane defaults for GN3_SECRETS to CD's secret file.  In CD,
    # this file is set in the genenetwork3 cd gexp:
    # https://git.genenetwork.org/gn-machines/tree/genenetwork-development.scm#n516
    # However, during testing GN3_SECRETS isn't set; and by default,
    # we run guix's default tests for python projects: `pytest`
    # https://git.genenetwork.org/guix-bioinformatics/tree/gn/packages/genenetwork.scm#n182
    if os.environ.get("GN3_SECRETS"):
        sparql_conf.from_envvar("GN3_SECRETS")
    # If the sparql configurations aren't loaded, set sane defaults.
    # This way, the genenetwork3 package builds.
    return {
        "sparql_user": sparql_conf.get("SPARQL_USER", "dba"),
        "sparql_auth_uri": sparql_conf.get(
            "SPARQL_AUTH_URI", "http://localhost:8890/sparql-auth/"
        ),
        "sparql_crud_auth_uri": sparql_conf.get(
            "SPARQL_CRUD_AUTH_URI", "http://localhost:8890/sparql-graph-crud-auth"
        ),
        "sparql_endpoint": sparql_conf.get("SPARQL_ENDPOINT", "http://localhost:8890"),
        "sparql_password": sparql_conf.get("SPARQL_PASSWORD", "dba"),
    }


# XXXX: Currently we run the tests against CD's virtuoso instance.
# This is not idempotent.  Consider having a special virtuoso instance
# just for running tests.
@pytest.fixture(scope="module")
def rdf_setup():
    """Upload RDF to a Virtuoso named graph"""
    # Define the URL and file
    sparql_conf = get_sparql_auth_conf()
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
