"""Version 1 API blueprint."""
from flask import Blueprint, url_for, jsonify, make_response

from .species import speciesbp

v1 = Blueprint("v1", __name__)
v1.register_blueprint(speciesbp, url_prefix="/species")


@v1.route("/", methods=["GET"])
def index():
    return make_response(jsonify({
        "message": (
            "This is v1 of the API. It's more hierarchical that the unversioned"
            " variant."),
        "links": {
            "self": url_for("v1.index"),
            "species": url_for("v1.species.list_species")
        }
    }), 200)
