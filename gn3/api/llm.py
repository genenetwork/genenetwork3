"""API for data used to generate menus"""

# pylint: skip-file

from flask import jsonify, request, Blueprint, current_app

from functools import wraps
from gn3.llms.process import get_gnqa
from gn3.llms.process import get_user_queries
from gn3.llms.process import fetch_query_results
from gn3.auth.authorisation.oauth2.resource_server import require_oauth
from gn3.auth import db
from gn3.settings import LLM_DB_PATH
from redis import Redis
import json
import sqlite3
from datetime import timedelta

GnQNA = Blueprint("GnQNA", __name__)


def handle_errors(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            return jsonify({"error": str(error)}), 500
    return decorated_function


@GnQNA.route("/gnqna", methods=["POST"])
def gnqa():
    # todo  add auth
    query = request.json.get("querygnqa", "")
    if not query:
        return jsonify({"error": "querygnqa is missing in the request"}), 400

    try:
        auth_token = current_app.config.get("FAHAMU_AUTH_TOKEN")
        task_id, answer, refs = get_gnqa(
            query, auth_token, current_app.config.get("DATA_DIR"))
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


@GnQNA.route("/rating/<task_id>", methods=["POST"])
@require_oauth("profile")
def rating(task_id):
    try:
        with (require_oauth.acquire("profile") as token,
              db.connection(LLM_DB_PATH) as conn):

            results = request.json
            user_id, query, answer, weight = (token.user.user_id,
                                              results.get("query"),
                                              results.get("answer"),
                                              results.get("weight", 0))
            cursor = conn.cursor()
            create_table = """CREATE TABLE IF NOT EXISTS Rating(
                  user_id TEXT NOT NULL,
                  query TEXT NOT NULL,
                  answer TEXT NOT NULL,
                  weight INTEGER NOT NULL DEFAULT 0,
                  task_id TEXT NOT NULL UNIQUE
                  )"""
            cursor.execute(create_table)
            cursor.execute("""INSERT INTO Rating(user_id,query,answer,weight,task_id)
            VALUES(?,?,?,?,?)
            ON CONFLICT(task_id) DO UPDATE SET
            weight=excluded.weight
            """, (str(user_id), query, answer, weight, task_id))
            return {
                "message": "success",
                "status": 0
            }, 200
    except sqlite3.Error as error:
        raise error
    except Exception as error:
        raise error


@GnQNA.route("/history/<query>", methods=["GET"])
@require_oauth("profile user")
@handle_errors
def fetch_user_hist(query):

    with (require_oauth.acquire("profile user") as the_token, Redis.from_url(current_app.config["REDIS_URI"],
                                                                             decode_responses=True) as redis_conn):
        return jsonify({
            **fetch_query_results(query, the_token.user.id, redis_conn),
            "prev_queries": get_user_queries("random_user", redis_conn)
        })


@GnQNA.route("/historys/<query>", methods=["GET"])
@handle_errors
def fetch_users_hist_records(query):
    """method to fetch all users hist:note this is a test functionality to be replaced by fetch_user_hist"""

    with Redis.from_url(current_app.config["REDIS_URI"], decode_responses=True) as redis_conn:
        return jsonify({
            **fetch_query_results(query, "random_user", redis_conn),
            "prev_queries": get_user_queries("random_user", redis_conn)
        })


@GnQNA.route("/get_hist_names", methods=["GET"])
@handle_errors
def fetch_prev_hist_ids():

    with (Redis.from_url(current_app.config["REDIS_URI"], decode_responses=True)) as redis_conn:
        return jsonify({"prev_queries": get_user_queries("random_user", redis_conn)})
