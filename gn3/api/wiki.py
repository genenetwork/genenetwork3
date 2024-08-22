import datetime
from flask import Blueprint, request, jsonify, current_app
from gn3 import db_utils

wiki = Blueprint("wiki", __name__)


@wiki.route("/comments/<int:comment_id>/edit", methods=["POST"])
def edit_wiki(comment_id: int):
    # FIXME: attempt to check and fix for types here with relevant errors
    payload = request.json
    pubmed_ids = [str(x) for x in payload.get("pubmed_ids", [])]

    insert_dict = {
        "Id": comment_id,
        "symbol": payload["symbol"],
        "PubMed_ID": " ".join(pubmed_ids),
        "comment": payload["comment"],
        # does this need to be part of the payload or can we get this from session information
        # e.g. https://github.com/genenetwork/genenetwork2/blob/0998033d0a7ea26ed96b00a360a334bae6de8c55/gn2/wqflask/oauth2/session.py#L22-L23
        "email": payload["email"],
        # DB doesn't default to now
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
        categories = get_categories(cursor)
        category_ids = []
        for category in payload["categories"]:
            cat_id = categories.get(category.strip())
            if cat_id is None:
                return jsonify(error=f"Error editting wiki entry, category with Name={category} not found"), 500
            category_ids.append(cat_id)
        cursor.execute("SELECT SpeciesID from Species  WHERE Name = %s", (payload["species"],))
        species_ids = cursor.fetchall()
        if len(species_ids) != 1:
            return jsonify(error=f"Error editting wiki entry, expected 1 species with Name={payload['species']} but found {len(species_ids)}!"), 500
        insert_dict["SpeciesID"] = species_ids[0][0]

        cursor.execute("SELECT MAX(versionId) as version_id from GeneRIF WHERE Id = %s", (comment_id,))
        latest_version = cursor.fetchone()[0]
        if latest_version is None:
            return jsonify(error=f"Error editting wiki entry, No comments found with comment_id={comment_id}"), 500
        insert_dict["versionId"] = latest_version + 1
        current_app.logger.debug(f"Running query: {insert_query}")
        cursor.execute(insert_query, insert_dict)

        category_addition_query = "INSERT INTO GeneRIFXRef (GeneRIFId, versionId, GeneCategoryId) VALUES (%s, %s, %s)"

        for cat_id in category_ids:
            current_app.logger.debug(f"Running query: {category_addition_query}")
            cursor.execute(category_addition_query, (comment_id, insert_dict["versionId"], cat_id))
        return jsonify({"success": "ok"})
    return jsonify(error="Error editting wiki entry, most likely due to DB error!"), 500


def get_categories(cursor) -> dict:
    cursor.execute("SELECT Name, Id from GeneCategory")
    raw_categories = cursor.fetchall()
    return dict(raw_categories)
