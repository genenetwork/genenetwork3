"""Test fixtures to set up a test named graph for loading RDF data."""
import pathlib
import os
import tempfile
import subprocess

from string import Template

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


@pytest.fixture(scope="session")
def rdf_setup():
    """Upload RDF to a Virtuoso named graph"""
    dir_path = pathlib.Path(__file__).parent.parent
    file_path = os.path.join(
        dir_path,
        "test_data/ttl-files/test-data.ttl",
    )
    with tempfile.TemporaryDirectory() as tmpdirname:
        init_file = os.path.join(tmpdirname, "virtuoso.ini")
        with open(init_file, "w", encoding="utf-8") as file_:
            file_.write(Template(VIRTUOSO_INI_FILE).substitute(
                dir_path=tmpdirname))
        # when using shell=True, pass in string as args, ref:
        # https://stackoverflow.com/a/10661488
        # pylint: disable-next=line-too-long
        command = f"virtuoso-t +foreground +wait +no-checkpoint +configfile {init_file}"
        with subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        ) as pid:
            while pid.stdout.readable():
                line = pid.stdout.readline()
                if not line:
                    raise RuntimeError("Something went wrong running virtuoso")
                # virtuoso is ready for connections
                if "server online at" in line.lower():
                    break
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
            pid.terminate()
