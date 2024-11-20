""" File contains the endpoints for calling rqtl2
"""
from flask import jsonify
from flask import Blueprint

rqtl2 = Blueprint("rqtl2", __name__)


@rqtl2.route("/compute", methods=["GET"])
def compute():
    """Init endpoint for computing qtl anaylsis using rqtl2"""
    # preprocessing data from the client
    # define required inputs
    return jsonify({"data": []})
