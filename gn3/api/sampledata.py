"""API for fetching sampledata from a given trait"""
import os
from flask import Blueprint
from flask import jsonify
from flask import current_app

from gn3.db.matrix import get_current_matrix
from gn3.db_utils import database_connection, dataset_is_public


sampledata = Blueprint("sampledata", __name__)


@sampledata.route("/dataset/<dataset_name>/trait/<trait_name>", methods=["GET"])
def get_sampledata(dataset_name, trait_name):
    """Fetch a trait's sampledata as a matrix."""
    with database_connection(current_app.config["SQL_URI"]) as conn, conn.cursor() as cursor:
        if not dataset_is_public(cursor, dataset_name):
            return jsonify(error="Dataset not found or not public"), 404
    return jsonify(
        get_current_matrix(
            os.path.join(
                current_app.config.get("LMDB_PATH"),
                dataset_name, trait_name
            )
        )
    )
