"""API for data used to generate menus"""

# pylint: skip-file

from flask import jsonify, request, Blueprint, current_app

from functools import wraps
from gn3.auth.authorisation.oauth2.resource_server import require_oauth

from gn3.llms.process import get_gnqa
from gn3.llms.process import fetch_query_results
from gn3.auth.authorisation.oauth2.resource_server import require_oauth
from gn3.auth import db
from gn3.settings import SQLITE_DB_PATH
from redis import Redis
import os
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
@require_oauth("profile")
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
        with (require_oauth.acquire("profile") as token, Redis.from_url(current_app.config["REDIS_URI"],
                                                                        decode_responses=True) as redis_conn):
            redis_conn.setex(
                f"LLM:{str(token.user.user_id)}-{query}", timedelta(days=10), json.dumps(response))
        return jsonify(response)
    except Exception as error:
        return jsonify({"query": query, "error": f"Request failed-{str(error)}"}), 500


@GnQNA.route("/rating/<task_id>", methods=["POST"])
@require_oauth("profile")
def rating(task_id):
    try:
        with require_oauth.acquire("profile") as token:
            results = request.json
            user_id, query, answer, weight = (str(token.user.user_id),
                                              results.get("query"),
                                              results.get("answer"),
                                              results.get("weight", 0))

            with db.connection(os.path.join(SQLITE_DB_PATH, "llm.db")) as conn:
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
                    "message": "Thanks for the Feedback"
                }, 200
    except sqlite3.Error as error:
        raise error


@GnQNA.route("/hist/titles", methods=["GET"])
@require_oauth("profile")
def fetch_history():
    with (require_oauth.acquire("profile") as token, Redis.from_url(current_app.config["REDIS_URI"],
                                                                    decode_responses=True) as redis_conn):

        records = [{result: result.rpartition(
            '-')[-1]} for result in redis_conn.keys(f"LLM:{str(token.user.user_id)}*")]
        return jsonify({
            "prev_queries": records
        })


@GnQNA.route("/history/<query>", methods=["GET"])
@require_oauth("profile")
def fetch_user_hist(query):
    with (require_oauth.acquire("profile") as token, Redis.from_url(current_app.config["REDIS_URI"],
                                                                    decode_responses=True) as redis_conn):
        return jsonify(fetch_query_results(query, redis_conn))
