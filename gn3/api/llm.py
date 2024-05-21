"""Api endpoints for gnqa"""
import json
import sqlite3
from redis import Redis

from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.llms.process import get_gnqa
from gn3.llms.errors import LLMError
from gn3.auth.authorisation.oauth2.resource_server import require_oauth

from gn3.auth import db

gnqa = Blueprint("gnqa", __name__)


@gnqa.route("/gnqna", methods=["POST"])
def gnqna():
    """Main gnqa endpoint"""
    query = request.json.get("querygnqa", "")
    if not query:
        return jsonify({"error": "querygnqa is missing in the request"}), 400

    try:
        fahamu_token = current_app.config.get("FAHAMU_AUTH_TOKEN")
        if fahamu_token is None:
            return jsonify({"query": query,
                            "error": "Use of invalid fahamu auth token"}), 500
        task_id, answer, refs = get_gnqa(
            query, fahamu_token, current_app.config.get("DATA_DIR"))
        response = {
            "task_id": task_id,
            "query": query,
            "answer": answer,
            "references": refs
        }
        try:
            with (Redis.from_url(current_app.config["REDIS_URI"],
                                 decode_responses=True) as redis_conn,
                  require_oauth.acquire("profile user") as token):
                redis_conn.set(
                    f"LLM:{str(token.user.user_id)}-{str(task_id['task_id'])}",
                    json.dumps(response)
                )
                return response
        except Exception:    # handle specific error
            return response
    except LLMError as error:
        return jsonify({"query": query,
                        "error": f"Request failed-{str(error)}"}), 500


@gnqa.route("/rating/<task_id>", methods=["POST"])
@require_oauth("profile")
def rating(task_id):
    """Endpoint for rating qnqa query and answer"""
    try:
        llm_db_path = current_app.config["LLM_DB_PATH"]
        with (require_oauth.acquire("profile") as token,
              db.connection(llm_db_path) as conn):

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
            cursor.execute("""INSERT INTO Rating(user_id,query,
            answer,weight,task_id)
            VALUES(?,?,?,?,?)
            ON CONFLICT(task_id) DO UPDATE SET
            weight=excluded.weight
            """, (str(user_id), query, answer, weight, task_id))
        return {
            "message":
            "You have successfully rated this query:Thank you!!"
        }, 200
    except sqlite3.Error as error:
        return jsonify({"error": str(error)}), 500


@gnqa.route("/searches", methods=["GET"])
@require_oauth("profile user")
def fetch_prev_searches():
    """ api method to fetch search query records"""
    with (require_oauth.acquire("profile user") as the_token,
          Redis.from_url(current_app.config["REDIS_URI"],
                         decode_responses=True) as redis_conn):
        if request.args.get("search_term"):
            return jsonify(json.loads(redis_conn.get(request.args.get("search_term"))))
        query_result = {}
        for key in redis_conn.scan_iter(f"LLM:{str(the_token.user.user_id)}*"):
            query_result[key] = json.loads(redis_conn.get(key))
        return jsonify(query_result)
