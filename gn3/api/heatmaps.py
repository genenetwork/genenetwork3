"""
Module to hold the entrypoint functions that generate heatmaps
"""

import io
from flask import jsonify
from flask import request
from flask import Blueprint
from gn3.heatmaps import build_heatmap
from gn3.db_utils import database_connector

heatmaps = Blueprint("heatmaps", __name__)

@heatmaps.route("/clustered", methods=("POST",))
def clustered_heatmaps():
    """
    Parses the incoming data and responds with the JSON-serialized plotly figure
    representing the clustered heatmap.
    """
    heatmap_request = request.get_json()
    traits_names = heatmap_request.get("traits_names", tuple())
    vertical = heatmap_request.get("vertical", False)
    if len(traits_names) < 2:
        return jsonify({
            "message": "You need to provide at least two trait names."
        }), 400
    conn, _cursor = database_connector()
    def parse_trait_fullname(trait):
        name_parts = trait.split(":")
        return "{dataset_name}::{trait_name}".format(
            dataset_name=name_parts[1], trait_name=name_parts[0])
    traits_fullnames = [parse_trait_fullname(trait) for trait in traits_names]

    with io.StringIO() as io_str:
        figure = build_heatmap(traits_fullnames, conn, vertical=vertical)
        figure.write_json(io_str)
        fig_json = io_str.getvalue()
    return fig_json, 200
