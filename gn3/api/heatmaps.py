from flask import jsonify
from flask import request
from flask import Blueprint
from gn3.heatmaps import build_heatmap
from gn3.db_utils import database_connector

heatmaps = Blueprint("heatmaps", __name__)

@heatmaps.route("/clustered", methods=("POST",))
def clustered_heatmaps():
    heatmap_request = request.get_json()
    traits_names = heatmap_request.get("traits_names", tuple())
    if len(traits_names) < 1:
        return jsonify({
            "message": "You need to provide at least one trait name."
        }), 400
    conn, _cursor = database_connector()
    def setup_trait_fullname(trait):
        name_parts = trait.split(":")
        return "{dataset_name}::{trait_name}".format(
            dataset_name=trait[1], trait_name=trait[0])
    traits_fullnames = [parse_trait_fullname(trait) for trait in traits_names]
    return jsonify(build_heatmap(traits_fullnames, conn)), 200
