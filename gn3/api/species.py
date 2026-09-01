"""Species API endpoints (v1)."""
from MySQLdb.cursors import DictCursor
from gn_libs.mysqldb import Connection, database_connection
from flask import (request,
                   jsonify,
                   url_for,
                   Blueprint,
                   make_response,
                   current_app as app)

from .populations import popbp

speciesbp = Blueprint("species", __name__)
speciesbp.register_blueprint(popbp, url_prefix="/<int:species_id>/populations")


def fetch_species(conn: Connection, detailed: bool = False) -> tuple[dict, ...]:
    """Fetch all the species that the system is aware of."""
    # 'Id' is needed for links to the Species, not very useful to end user.
    _detailed = ("Id", "SpeciesId", "SpeciesName", "Name", "MenuName",
                 "FullName", "TaxonomyId",  "OrderId", "Family",
                 "FamilyOrderId")
    _summary = ("Id", "SpeciesName", "Name", "FullName")
    columns = ", ".join(_detailed if detailed else _summary)
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(f"SELECT {columns} FROM Species ORDER BY Species.Id")
        return tuple(dict(row) for row in cursor.fetchall())


@speciesbp.route("/", methods=["GET"])
def list_species():
    with database_connection(app.config["SQL_URI"]) as conn:
        species_list = fetch_species(
            conn,
            detailed=str(request.args.get("detailed") or "").lower() == "true")
        return make_response(jsonify({
            "status": "success",
            "message": (
                "The listing of species that this system is aware of."
                "\n\nA GET parameter 'detailed=true' can be provided to provide"
                " more detailed, albeit noisy, output."),
            "species": [{
                **{key: val for key,val in spc.items() if key not in ("Id",)},
                "links": {
                    "self": url_for(
                        "v1.species.species_details", species_id=spc["Id"])
                }
            } for spc in species_list],
            "links": {
                "self": url_for("v1.species.list_species")
            }
        }), 200)


@speciesbp.route("/<int:species_id>", methods=["GET"])
def species_details(species_id: int):
    return make_response(jsonify({
        "status": "not implemented",
        "message": (
            "Species details are not yet available under this API version."),
        "links": {
            "self": url_for(
                "v1.species.species_details", species_id=species_id),
            "collection": url_for("v1.species.list_species"),
            "populations": url_for("v1.species.populations.list_populations",
                                   species_id=species_id),
        }
    }), 501)
