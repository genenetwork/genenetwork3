"""Test fixtures to set up a test named graph for loading RDF data."""
import os
import tempfile
import subprocess

from string import Template

import psutil  # type: ignore
import pytest
import requests
from requests.auth import HTTPDigestAuth

from tests.fixtures.virtuoso import VIRTUOSO_INI_FILE


SPARQL_CONF = {
    "sparql_user": "dba",
    "sparql_password": "dba",
    "sparql_auth_uri": "http://localhost:8191/sparql-auth/",
    "sparql_crud_auth_uri": "http://localhost:8191/sparql-graph-crud-auth/",
    "sparql_endpoint": "http://localhost:8191/sparql/",
}


def get_process_id(name) -> list:
    """Return process ids found by (partial) name or regex.

    >>> get_process_id('kthreadd')
    [2]
    >>> get_process_id('watchdog')
    [10, 11, 16, 21, 26, 31, 36, 41, 46, 51, 56, 61]  # ymmv
    >>> get_process_id('non-existent process')
    []
    """
    with subprocess.Popen(
        ["pgrep", "-f", name], stdout=subprocess.PIPE, shell=False
    ) as proc:
        response = proc.communicate()[0]
        return [int(pid) for pid in response.split()]


@pytest.fixture(scope="session")
def rdf_setup():
    """Upload RDF to a Virtuoso named graph"""
    dir_path = os.path.dirname(__file__).split("fixtures")[0]
    file_path = os.path.join(
        dir_path,
        "test_data/ttl-files/test-data.ttl",
    )
    # We intentionally use a temporary directory.  This way, all the
    # database created by virtuoso are cleaned after running tests.
    with tempfile.TemporaryDirectory() as tmpdirname:
        init_file = os.path.join(tmpdirname, "virtuoso.ini")
        # Create the virtuoso init file which we use when
        # bootstrapping virtuoso.
        with open(init_file, "w", encoding="utf-8") as file_:
            file_.write(Template(VIRTUOSO_INI_FILE).substitute(
                dir_path=tmpdirname))
        # Here we intentionally ignore the "+foreground" option to
        # allow virtuoso to run in the background.
        with subprocess.Popen(
            [
                "virtuoso-t",
                "+wait",
                "+no-checkpoint",
                "+configfile",
                init_file,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ) as pid:
            pid.wait()
            # Define the query parameters and authentication
            params = {"graph": "http://cd-test.genenetwork.org"}
            auth = HTTPDigestAuth("dba", "dba")

            # Make sure this graph does not exist before running anything
            requests.delete(
                SPARQL_CONF["sparql_crud_auth_uri"], params=params, auth=auth
            )

            # Open the file in binary mode and send the request
            with open(file_path, "rb") as file:
                response = requests.put(
                    SPARQL_CONF["sparql_crud_auth_uri"],
                    params=params,
                    auth=auth,
                    data=file,
                )
            yield response
            requests.delete(
                SPARQL_CONF["sparql_crud_auth_uri"], params=params, auth=auth
            )
            for pid_ in get_process_id(init_file):
                psutil.Process(pid_).kill()
