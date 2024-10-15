"""API for accessing/editing rif/wiki metadata"""

import datetime
from typing import Any, Dict

from flask import Blueprint, request, jsonify, current_app, make_response

from gn3 import db_utils
from gn3.oauth2.authorisation import require_token
from gn3.db import wiki
from gn3.db.rdf.wiki import (
    get_wiki_entries_by_symbol,
    get_comment_history,
    update_wiki_comment,
    get_rif_entries_by_symbol,
)


wiki_blueprint = Blueprint("wiki", __name__, url_prefix="wiki")
rif_blueprint = Blueprint("rif", __name__, url_prefix="rif")


@wiki_blueprint.route("/<int:comment_id>/edit", methods=["POST"])
@require_token
def edit_wiki(comment_id: int, **kwargs):
    """Edit wiki comment. This is achieved by adding another entry with a new VersionId"""
    # FIXME: attempt to check and fix for types here with relevant errors
    payload: Dict[str, Any] = request.json  # type: ignore
    pubmed_ids = [str(x) for x in payload.get("pubmed_ids", [])]
    insert_dict = {
        "Id": comment_id,
        "symbol": payload["symbol"],
        "PubMed_ID": " ".join(pubmed_ids),
        "comment": payload["comment"],
        "email": payload["email"],
        "createtime": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "user_ip": request.environ.get("HTTP_X_REAL_IP", request.remote_addr),
        "weburl": payload.get("web_url"),
        "initial": payload.get("initial"),
        "reason": payload["reason"],
        "species": payload["species"],
        "categories": payload["categories"],
    }

    insert_query = """
    INSERT INTO GeneRIF (Id, versionId, symbol, PubMed_ID, SpeciesID, comment,
                         email, createtime, user_ip, weburl, initial, reason)
    VALUES (%(Id)s, %(versionId)s, %(symbol)s, %(PubMed_ID)s, %(SpeciesID)s, %(comment)s, %(email)s, %(createtime)s, %(user_ip)s, %(weburl)s, %(initial)s, %(reason)s)
    """
    with db_utils.database_connection(current_app.config["SQL_URI"]) as conn:
        cursor = conn.cursor()
        next_version = 0
        try:
            category_ids = wiki.get_categories_ids(
                cursor, payload["categories"])
            species_id = wiki.get_species_id(cursor, payload["species"])
            next_version = wiki.get_next_comment_version(cursor, comment_id)
        except wiki.MissingDBDataException as missing_exc:
            return jsonify(error=f"Error editing wiki entry, {missing_exc}"), 500
        insert_dict["SpeciesID"] = species_id
        insert_dict["versionId"] = next_version
        current_app.logger.debug(f"Running query: {insert_query}")
        cursor.execute(insert_query, insert_dict)
        category_addition_query = """
            INSERT INTO GeneRIFXRef (GeneRIFId, versionId, GeneCategoryId)
                VALUES (%s, %s, %s)
            """

        for cat_id in category_ids:
            current_app.logger.debug(
                f"Running query: {category_addition_query}")
            cursor.execute(
                category_addition_query, (comment_id,
                                          insert_dict["versionId"], cat_id)
            )

        try:
            # Editing RDF:
            update_wiki_comment(
                insert_dict=insert_dict,
                sparql_user=current_app.config["SPARQL_USER"],
                sparql_password=current_app.config["SPARQL_PASSWORD"],
                sparql_auth_uri=current_app.config["SPARQL_AUTH_URI"]
            )
        except Exception as exc:
            conn.rollback()  # type: ignore
            raise exc
        return jsonify({"success": "ok"})
    return jsonify(error="Error editing wiki entry, most likely due to DB error!"), 500


@wiki_blueprint.route("/<string:symbol>", methods=["GET"])
def get_wiki_entries(symbol: str):
    """Fetch wiki entries"""
    status_code = 200
    response = get_wiki_entries_by_symbol(
        symbol=symbol,
        sparql_uri=current_app.config["SPARQL_ENDPOINT"])
    data = response.get("data")
    if not data:
        data = {}
        status_code = 404
    if request.headers.get("Accept") == "application/ld+json":
        payload = make_response(response)
        payload.headers["Content-Type"] = "application/ld+json"
        return payload, status_code
    return jsonify(data), status_code


@wiki_blueprint.route("/<int:comment_id>", methods=["GET"])
def get_wiki(comment_id: int):
    """
    Gets latest wiki comments.

    TODO: fetch this from RIF
    """
    with db_utils.database_connection(current_app.config["SQL_URI"]) as conn:
        return jsonify(wiki.get_latest_comment(conn, comment_id))
    return jsonify(error="Error fetching wiki entry, most likely due to DB error!"), 500


@wiki_blueprint.route("/categories", methods=["GET"])
def get_categories():
    """ Gets list of supported categories for RIF """
    with db_utils.database_connection(current_app.config["SQL_URI"]) as conn:
        cursor = conn.cursor()
        categories_dict = wiki.get_categories(cursor)
        return jsonify(categories_dict)
    return jsonify(error="Error getting categories, most likely due to DB error!"), 500


@wiki_blueprint.route("/species", methods=["GET"])
def get_species():
    """ Gets list of all species, contains name and SpeciesName """
    with db_utils.database_connection(current_app.config["SQL_URI"]) as conn:
        cursor = conn.cursor()
        species_dict = wiki.get_species(cursor)
        return jsonify(species_dict)
    return jsonify(error="Error getting species, most likely due to DB error!"), 500


@wiki_blueprint.route("/<int:comment_id>/history", methods=["GET"])
def get_history(comment_id):
    """Fetch all of a given comment's history given it's comment id"""
    status_code = 200
    response = get_comment_history(comment_id=comment_id,
                                   sparql_uri=current_app.config["SPARQL_ENDPOINT"])
    data = response.get("data")
    if not data:
        data = {}
        status_code = 404
    if request.headers.get("Accept") == "application/ld+json":
        payload = make_response(response)
        payload.headers["Content-Type"] = "application/ld+json"
        return payload, status_code
    return jsonify(data), status_code


@rif_blueprint.route("/<string:symbol>", methods=["GET"])
def get_ncbi_rif_entries(symbol: str):
    """Fetch NCBI RIF entries"""
    status_code = 200
    response = get_rif_entries_by_symbol(
        symbol,
        sparql_uri=current_app.config["SPARQL_ENDPOINT"])
    data = response.get("data")
    if not data:
        data, status_code = {}, 404
    if request.headers.get("Accept") == "application/ld+json":
        payload = make_response(response)
        payload.headers["Content-Type"] = "application/ld+json"
        return payload, status_code
    return jsonify(data), status_code
