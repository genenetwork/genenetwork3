"""Test fixtures to set up a test named graph for loading RDF data."""
import os
from requests.auth import HTTPDigestAuth
from flask import config
import requests
import pytest


def get_sparql_auth_conf() -> dict:
    """Fetch SPARQL auth configuration for the GN3_SECRETS file."""
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
    if not os.environ.get("GN3_SECRETS"):
        os.environ["GN3_SECRETS"] = "/etc/genenetwork/conf/gn3/secrets.py"
    sparql_conf.from_envvar("GN3_SECRETS")
    return {
        "sparql_user": sparql_conf["SPARQL_USER"],
        "sparql_auth_uri": sparql_conf["SPARQL_AUTH_URI"],
        "sparql_crud_auth_uri": sparql_conf["SPARQL_CRUD_AUTH_URI"],
        "sparql_endpoint": sparql_conf["SPARQL_ENDPOINT"],
        "sparql_password": sparql_conf["SPARQL_PASSWORD"],
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
