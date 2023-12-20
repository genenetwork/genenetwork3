from flask import request
from flask import Blueprint
from process import getGNQA

llm = Blueprint("llm", __name__)

@llm.route("/gnqa", methods=["POST"])
def gnqa():
    query = request.form.get("querygnqa", "")
    if not query:
        return jsonify({"error": "querygnqa is missing in the request"}), 400
    answer, accordion_refs = getGNQA(query)
    return jsonify({
        "query": query,
        "answer": answer,
        "accordion_refs": accordion_refs
    })
