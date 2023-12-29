"""API for data used to generate menus"""

# pylint: skip-file

from flask import jsonify, request, Blueprint

from gn3.llms.process import getGNQA

GnQNA = Blueprint("GnQNA", __name__)


@GnQNA.route("/gnqna", methods=["POST"])
def gnqa():
    query = request.json.get("querygnqa", "")
    if not query:
        return jsonify({"error": "querygnqa is missing in the request"}), 400

    try:
        answer, refs = getGNQA(query)
        return jsonify({
            "query": query,
            "answer": answer,
            "references": refs
        })

    except Exception as error:
        return jsonify({"query": query, "error": "Internal server error"}), 500
