import datetime
from flask import Blueprint, request, jsonify, current_app
from gn3 import db_utils

wiki = Blueprint("wiki", __name__)


@wiki.route("/comments/<int:comment_id>/edit", methods=["POST"])
def edit_wiki(comment_id: int):
    payload = request.json
    insert_dict = {
        "Id": comment_id,
        "versionId": payload["version_id"],
        "symbol": payload["symbol"],
        "PubMed_ID": payload.get("pubmed_id"),
        "SpeciesID": payload["species_id"],
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

    if not isinstance(insert_dict["versionId"], int):
        return jsonify(
            error=f"Error editting wiki entry, expected versionId as int but got {insert_dict['versionId']}!"
        ), 500
    if not isinstance(insert_dict["SpeciesID"], int):
        return jsonify(
            error=f"Error editting wiki entry, expected versionId as int but got {insert_dict['SpeciesID']}!"
        ), 500

    insert_query = """
    INSERT INTO GeneRIF (Id, versionId, symbol, PubMed_ID, SpeciesID, comment,
                         email, createtime, user_ip, weburl, initial, reason)
    VALUES (%(Id)s, %(versionId)s, %(symbol)s, %(PubMed_ID)s, %(SpeciesID)s, %(comment)s, %(email)s, %(createtime)s, %(user_ip)s, %(weburl)s, %(initial)s, %(reason)s)
    """
    with db_utils.database_connection(current_app.config["SQL_URI"]) as conn:
        cursor = conn.cursor()
        current_app.logger.error(f"Inserting: {insert_dict}")
        current_app.logger.error(f"wiht query: {insert_query}")
        cursor.execute(insert_query, insert_dict)
        return jsonify({"success": "ok"})
    return jsonify(error="Error editting wiki entry, most likely due to DB error!"), 500
