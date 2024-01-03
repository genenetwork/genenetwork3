"""API for data used to generate menus"""

# pylint: skip-file

from flask import jsonify, request, Blueprint, current_app

from gn3.llms.process import getGNQA

GnQNA = Blueprint("GnQNA", __name__)


@GnQNA.route("/gnqna", methods=["POST"])
def gnqa():
    query = request.json.get("querygnqa", "")
    if not query:
        return jsonify({"error": "querygnqa is missing in the request"}), 400

    try:
        auth_token = current_app.config.get("FAHAMU_AUTH_TOKEN")
        answer, refs = getGNQA(
            query, auth_token)

        return jsonify({
            "query": query,
            "answer": answer,
            "references": refs
        })

    except Exception as error:
        return jsonify({"query": query, "error": "Internal server error"}), 500
