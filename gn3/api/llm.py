"""API for data used to generate menus"""

from flask import jsonify, request, Blueprint

from gn3.llms.process import getGNQA

GnQNA = Blueprint("GnQNA", __name__)


@GnQNA.route("/gnqna", methods=["POST"])
def gnqa():
    query = request.json.get("querygnqa", "")
    if not query:
        return jsonify({"error": "querygnqa is missing in the request"}), 400
    answer, refs = getGNQA(query)
    return jsonify({
        "query": query,
        "answer": answer,
        "references": refs
    })
