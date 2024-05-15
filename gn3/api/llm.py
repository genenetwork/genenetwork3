"""Api endpoints for gnqa"""
from datetime import timedelta
from functools import wraps
import json
import sqlite3
from redis import Redis

from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.llms.process import get_gnqa
from gn3.llms.process import get_user_queries
from gn3.llms.process import fetch_query_results
from gn3.auth.authorisation.oauth2.resource_server import require_oauth
from gn3.auth import db

GnQNA = Blueprint("GnQNA", __name__)


def handle_errors(func):
    """general error handling decorator function"""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as error:
            return jsonify({"error": str(error)}), 500
    return decorated_function


@GnQNA.route("/gnqna", methods=["POST"])
def gnqa():
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
        with (Redis.from_url(current_app.config["REDIS_URI"],
                             decode_responses=True) as redis_conn):
            redis_conn.setex(
                f"LLM:random_user-{query}",
                timedelta(days=10), json.dumps(response))
        return jsonify({
            **response,
            "prev_queries": get_user_queries("random_user", redis_conn)
        })
    except Exception as error:
        return jsonify({"query": query,
                        "error": f"Request failed-{str(error)}"}), 500


@GnQNA.route("/rating/<task_id>", methods=["POST"])
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
    except Exception as error:
        raise error


@GnQNA.route("/history/<query>", methods=["GET"])
@require_oauth("profile user")
@handle_errors
def fetch_user_hist(query):
    """"Endpoint to fetch previos searches for User"""
    with (require_oauth.acquire("profile user") as the_token,
          Redis.from_url(current_app.config["REDIS_URI"],
          decode_responses=True) as redis_conn):
        return jsonify({
            **fetch_query_results(query, the_token.user.id, redis_conn),
            "prev_queries": get_user_queries("random_user", redis_conn)
        })


@GnQNA.route("/historys/<query>", methods=["GET"])
@handle_errors
def fetch_users_hist_records(query):
    """method to fetch all users hist:note this is a test functionality
    to be replaced by fetch_user_hist
    """

    with Redis.from_url(current_app.config["REDIS_URI"],
                        decode_responses=True) as redis_conn:
        return jsonify({
            **fetch_query_results(query, "random_user", redis_conn),
            "prev_queries": get_user_queries("random_user", redis_conn)
        })


@GnQNA.route("/get_hist_names", methods=["GET"])
@handle_errors
def fetch_prev_hist_ids():
    """Test method for fetching history for Anony Users"""
    with (Redis.from_url(current_app.config["REDIS_URI"],
                         decode_responses=True)) as redis_conn:
        return jsonify({"prev_queries": get_user_queries("random_user",
                                                         redis_conn)})
