"""API for data used to generate menus"""

# pylint: skip-file

from flask import jsonify, request, Blueprint, current_app
from gn3.auth.authorisation.oauth2.resource_server import require_oauth

from gn3.llms.process import get_gnqa
from gn3.llms.process import rate_document
from gn3.llms.process import get_user_queries
from gn3.llms.process import fetch_query_results

from redis import Redis
import json
from datetime import timedelta

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

        response = {
            "task_id": task_id,
            "query": query,
            "answer": answer,
            "references": refs
        }
        with (Redis.from_url(current_app.config["REDIS_URI"],
                             decode_responses=True) as redis_conn):
            # The key will be deleted after 60 seconds
            redis_conn.setex(f"LLM:random_user-{query}", timedelta(days=10), json.dumps(response))
        return jsonify({
            **response,
            "prev_queries": get_user_queries("random_user", redis_conn)
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


@GnQNA.route("/history/<query>", methods=["GET"])
@require_oauth("profile user")
def fetch_user_hist(query):
    try:

        with (require_oauth.acquire("profile user") as the_token, Redis.from_url(current_app.config["REDIS_URI"],
                                                                                 decode_responses=True) as redis_conn):
            return jsonify({
                **fetch_query_results(query, the_token.user.id, redis_conn),
                "prev_queries": get_user_queries("random_user", redis_conn)
            })

    except Exception as error:
        return jsonify({"error": str(error)}), 500


@GnQNA.route("/historys/<query>", methods=["GET"])
def fetch_users_hist_records(query):
    """method to fetch all users hist:note this is a test functionality to be replaced by fetch_user_hist"""
    try:

        with Redis.from_url(current_app.config["REDIS_URI"], decode_responses=True) as redis_conn:
            return jsonify({
                **fetch_query_results(query, "random_user", redis_conn),
                "prev_queries": get_user_queries("random_user", redis_conn)
            })

    except Exception as error:
        return jsonify({"error": str(error)}), 500


@GnQNA.route("/get_hist_names", methods=["GET"])
def fetch_prev_hist_ids():
    try:
        with (Redis.from_url(current_app.config["REDIS_URI"], decode_responses=True)) as redis_conn:
            return jsonify({"prev_queries": get_user_queries("random_user", redis_conn)})

    except Exception as error:
        return jsonify({"error": str(error)}), 500
