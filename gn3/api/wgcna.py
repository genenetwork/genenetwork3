"""endpoint to run wgcna analysis"""
from flask import Blueprint
from flask import request
from flask import current_app
from flask import jsonify

from gn3.computations.wgcna import call_wgcna_script

wgcna = Blueprint("wgcna", __name__)


@wgcna.route("/run_wgcna", methods=["POST"])
def run_wgcna():
    """run wgcna:output should be a json with a the data"""

    wgcna_data = request.json

    wgcna_script = current_app.config["WGCNA_RSCRIPT"]

    results = call_wgcna_script(wgcna_script, wgcna_data)

    return jsonify(results), 200
