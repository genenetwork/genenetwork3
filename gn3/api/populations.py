"""Population (InbredSet group) API endpoints (v1)."""
from flask import Blueprint, jsonify, make_response, url_for

from .case_attributes import caseattrsbp

popbp = Blueprint("populations", __name__)
popbp.register_blueprint(caseattrsbp, url_prefix="/<int:pop_id>/case-attributes")


@popbp.route("/", methods=["GET"])
def list_populations(species_id: int):
    return make_response(jsonify({
        "status": "not implemented",
        "message": "Population listing is not yet available under this API version.",
        "links": {
            "self": url_for("v1.species.populations.list_populations",
                            species_id=species_id),
            "species": url_for("v1.species.species_details",
                               species_id=species_id),
        }
    }), 501)


@popbp.route("/<int:pop_id>", methods=["GET"])
def population_details(species_id: int, pop_id: int):
    return make_response(jsonify({
        "status": "not implemented",
        "message": "Population details are not yet available under this API version.",
        "links": {
            "self": url_for("v1.species.populations.population_details",
                            species_id=species_id, pop_id=pop_id),
            "species": url_for("v1.species.species_details",
                               species_id=species_id),
            "case-attributes": url_for(
                "v1.species.populations.case-attributes.v1_list_case_attributes",
                species_id=species_id, pop_id=pop_id),
        }
    }), 501)
