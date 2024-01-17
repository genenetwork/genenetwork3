"""API for data used to generate menus"""

# pylint: skip-file

from flask import jsonify, request, Blueprint, current_app

from gn3.llms.process import get_gnqa

from gn3.llms.process import rate_document

GnQNA = Blueprint("GnQNA", __name__)


@GnQNA.route("/gnqna", methods=["POST"])
def gnqa():
    query = request.json.get("querygnqa", "")
    if not query:
        return jsonify({"error": "querygnqa is missing in the request"}), 400

    try:
        auth_token = current_app.config.get("FAHAMU_AUTH_TOKEN")
        task_id, answer, refs = get_gnqa(
            query, auth_token)

        return jsonify({
            "task_id": task_id,
            "query": query,
            "answer": answer,
            "references": refs
        })

    except Exception as error:
        return jsonify({"query": query, "error": f"Request failed-{str(error)}"}), 500


@GnQNA.route("/rating/<task_id>/<doc_id>/<int:rating>", methods=["POST"])
def rating(task_id, doc_id, rating):
    try:
        results = rate_document(task_id, doc_id, rating,
                                current_app.config.get("FAHAMU_AUTH_TOKEN"))

        return jsonify({
            **results,
            "doc_id": doc_id,
            "task_id": task_id,
        }),
    except Exception as error:
        return jsonify({"error": str(error), doc_id: doc_id}), 500
