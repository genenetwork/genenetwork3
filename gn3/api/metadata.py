"""API for fetching metadata using an API"""
from http.client import RemoteDisconnected
from urllib.error import URLError
from flask import Blueprint
from flask import jsonify
from flask import current_app

from SPARQLWrapper import SPARQLWrapper

from gn3.db.rdf import get_dataset_metadata


metadata = Blueprint("metadata", __name__)


@metadata.route("/dataset/<accession_id>", methods=["GET"])
def jsonify_dataset_metadata(accession_id):
    """Fetch a dataset's metadata given it's ACCESSION_ID"""
    try:
        return jsonify(
            get_dataset_metadata(
                SPARQLWrapper(current_app.config.get("SPARQL_ENDPOINT")),
                accession_id,
            ).data
        )
    # The virtuoso server is misconfigured or it isn't running at all
    except (RemoteDisconnected, URLError):
        return jsonify({})
