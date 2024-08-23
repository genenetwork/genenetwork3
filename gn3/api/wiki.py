import datetime
from typing import Any, Dict, List
from flask import Blueprint, request, jsonify, current_app
from gn3 import db_utils


wiki = Blueprint("wiki", __name__)


class MissingDBDataException(Exception):
    pass


@wiki.route("/<int:comment_id>/edit", methods=["POST"])
def edit_wiki(comment_id: int):
    # FIXME: attempt to check and fix for types here with relevant errors
    payload: Dict[str, Any] = request.json
    pubmed_ids = [str(x) for x in payload.get("pubmed_ids", [])]

    insert_dict = {
        "Id": comment_id,
        "symbol": payload["symbol"],
        "PubMed_ID": " ".join(pubmed_ids),
        "comment": payload["comment"],
        "email": payload["email"],
        "createtime": datetime.datetime.now(datetime.timezone.utc).strftime(
            "%Y-%m-%d %H:%M"
        ),
        "user_ip": request.environ.get("HTTP_X_REAL_IP", request.remote_addr),
        "weburl": payload.get("web_url"),
        "initial": payload.get("initial"),
        "reason": payload["reason"],
    }

    insert_query = """
    INSERT INTO GeneRIF (Id, versionId, symbol, PubMed_ID, SpeciesID, comment,
                         email, createtime, user_ip, weburl, initial, reason)
    VALUES (%(Id)s, %(versionId)s, %(symbol)s, %(PubMed_ID)s, %(SpeciesID)s, %(comment)s, %(email)s, %(createtime)s, %(user_ip)s, %(weburl)s, %(initial)s, %(reason)s)
    """
    with db_utils.database_connection(current_app.config["SQL_URI"]) as conn:
        cursor = conn.cursor()
        try:
            category_ids = get_categories_ids(cursor, payload["categories"])
            species_id = get_species_id(cursor, payload["species"])
            next_version = get_next_comment_version(cursor, comment_id)
        except MissingDBDataException as missing_exc:
            return jsonify(error=f"Error editting wiki entry, {missing_exc}"), 500
        insert_dict["SpeciesID"] = species_id
        insert_dict["versionId"] = next_version
        current_app.logger.debug(f"Running query: {insert_query}")
        cursor.execute(insert_query, insert_dict)
        category_addition_query = "INSERT INTO GeneRIFXRef (GeneRIFId, versionId, GeneCategoryId) VALUES (%s, %s, %s)"

        for cat_id in category_ids:
            current_app.logger.debug(f"Running query: {category_addition_query}")
            cursor.execute(
                category_addition_query, (comment_id, insert_dict["versionId"], cat_id)
            )
        return jsonify({"success": "ok"})
    return jsonify(error="Error editting wiki entry, most likely due to DB error!"), 500


def get_species_id(cursor, species_name: str) -> int:
    cursor.execute("SELECT SpeciesID from Species  WHERE Name = %s", (species_name,))
    species_ids = cursor.fetchall()
    if len(species_ids) != 1:
        raise MissingDBDataException(
            f"expected 1 species with Name={species_name} but found {len(species_ids)}!"
        )
    return species_ids[0][0]


def get_next_comment_version(cursor, comment_id: int) -> int:
    cursor.execute(
        "SELECT MAX(versionId) as version_id from GeneRIF WHERE Id = %s", (comment_id,)
    )
    latest_version = cursor.fetchone()[0]
    if latest_version is None:
        raise MissingDBDataException(f"No comment found with comment_id={comment_id}")
    return latest_version + 1


def get_categories_ids(cursor, categories: List[str]) -> List[int]:
    cursor.execute("SELECT Name, Id from GeneCategory")
    raw_categories = cursor.fetchall()
    dict_cats = dict(raw_categories)
    category_ids = []
    for category in set(categories):
        cat_id = dict_cats.get(category.strip())
        if cat_id is None:
            raise MissingDBDataException(f"Category with Name={category} not found")
        category_ids.append(cat_id)
    return category_ids
