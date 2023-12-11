from flask import request
from flask import Blueprint
from process import getGNQA
from oauth import authenticator

llm = Blueprint("llm", __name__)


@llm.route("/gnqa", methods=["POST"])
@authenticator
def gnqa(current_user):
    """Entry route for gn-llm """
    if not current_user:
        return jsonify({"error": "user needs to be authenticated"}), 403
    query = request.form.get("querygnqa", "")
    if not query:
        return jsonify({"error": "querygnqa is missing in the request"}), 400
    answer, accordion_refs = getGNQA(query)
    return jsonify({
        "query": query,
        "answer": answer,
        "accordion_refs": accordion_refs
    })
