"""API for fetching sampledata from a given trait"""
import os
from flask import Blueprint
from flask import jsonify
from flask import current_app

from gn3.db.matrix import get_current_matrix


sampledata = Blueprint("sampledata", __name__)


@sampledata.route("/dataset/<dataset_name>/trait/<trait_name>", methods=["GET"])
def get_sampledata(dataset_name, trait_name):
    """Fetch a trait's sampledata as a matrix."""
    return jsonify(
        get_current_matrix(
            os.path.join(
                current_app.config.get("LMDB_PATH"),
                dataset_name, trait_name
            )
        )
    )
