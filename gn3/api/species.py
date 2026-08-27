"""Species API endpoints (v1)."""
from flask import Blueprint, jsonify, make_response, url_for

from .populations import popbp

speciesbp = Blueprint("species", __name__)
speciesbp.register_blueprint(popbp, url_prefix="/<int:species_id>/populations")


@speciesbp.route("/", methods=["GET"])
def list_species():
    return make_response(jsonify({
        "status": "not implemented",
        "message": "Species listing is not yet available under this API version.",
        "links": {
            "self": url_for("v1.species.list_species"),
        }
    }), 501)


@speciesbp.route("/<int:species_id>", methods=["GET"])
def species_details(species_id: int):
    return make_response(jsonify({
        "status": "not implemented",
        "message": "Species details are not yet available under this API version.",
        "links": {
            "self": url_for("v1.species.species_details",
                            species_id=species_id),
            "populations": url_for("v1.species.populations.list_populations",
                                   species_id=species_id),
        }
    }), 501)
