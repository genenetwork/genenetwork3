"""API for fetching metadata using an API"""
from http.client import RemoteDisconnected
from urllib.error import URLError
from flask import Blueprint
from flask import jsonify
from flask import current_app

from SPARQLWrapper import SPARQLWrapper

from gn3.db.rdf import get_dataset_metadata
from gn3.db.rdf import get_trait_metadata


metadata = Blueprint("metadata", __name__)


@metadata.route("/dataset/<name>", methods=["GET"])
def dataset_metadata(name):
    """Fetch a dataset's metadata given it's ACCESSION_ID"""
    try:
        return jsonify(
            get_dataset_metadata(
                SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT")),
                name,
            ).data
        )
    # The virtuoso server is misconfigured or it isn't running at all
    except (RemoteDisconnected, URLError):
        return jsonify({})


@metadata.route("/dataset/<dataset_name>/trait/<trait_name>", methods=["GET"])
def trait_metadata(dataset_name, trait_name):
    """Fetch a trait's metadata given the trait_name and dataset_name'"""
    try:
        return jsonify(
            get_trait_metadata(
                SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT")),
                trait_name, dataset_name
            ).data
        )
    # The virtuoso server is misconfigured or it isn't running at all
    except (RemoteDisconnected, URLError):
        return jsonify({})
