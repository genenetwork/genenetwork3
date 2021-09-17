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
    _heatmap_file, heatmap_fig = build_heatmap(traits_names, conn)

    # stream the heatmap data somehow here.
    # Can plotly actually stream the figure data in a way that can be used on
    # remote end to display the image without necessarily being html?
    # return jsonify(
    #     {
    #         "query": heatmap_request,
    #         "output_png": heatmap_fig.to_image(format="png"),
    #         "output_svg": heatmap_fig.to_image(format="svg")
    #     }), 200
    return jsonify({"output_filename": _heatmap_file}), 200
