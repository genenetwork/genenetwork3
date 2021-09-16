"""endpoint to run wgcna analysis"""
from flask import Blueprint
from flask import request

wgcna = Blueprint("wgcna", __name__)


@wgcna.route("/run_wgcna", methods=["POST"])
def run_wgcna():

    _wgcna_data = request.json

    return "success", 200
