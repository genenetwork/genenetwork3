"""Api endpoints for gnqa"""
import json
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.llms.process import get_gnqa
from gn3.llms.errors import LLMError
from gn3.auth.authorisation.oauth2.resource_server import require_oauth
from gn3.auth import db


gnqa = Blueprint("gnqa", __name__)


@gnqa.route("/search", methods=["PUT"])
def search():
    """Api  endpoint for searching queries in fahamu Api"""
    query = request.json.get("querygnqa", "")
    if not query:
        return jsonify({"error": "querygnqa is missing in the request"}), 400
    fahamu_token = current_app.config.get("FAHAMU_AUTH_TOKEN")
    if not fahamu_token:
        raise LLMError(
            "Request failed: an LLM authorisation token  is required ", query)
    task_id, answer, refs = get_gnqa(
        query, fahamu_token, current_app.config.get("DATA_DIR"))
    response = {
        "task_id": task_id,
        "query": query,
        "answer": answer,
        "references": refs
    }
    with (db.connection(current_app.config["LLM_DB_PATH"]) as conn,
          require_oauth.acquire("profile user") as token):
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS
        history(user_id TEXT NOT NULL,
        task_id TEXT NOT NULL,
        query  TEXT NOT NULL,
        results  JSONB,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(task_id)) WITHOUT ROWID""")
        cursor.execute(
            """INSERT INTO history(user_id, task_id, query, results)
            VALUES(?, ?, ?, ?)
            """, (str(token.user.user_id), str(task_id["task_id"]),
                  query,
                  json.dumps(response))
        )
    return response


@gnqa.route("/rating/<task_id>", methods=["POST"])
@require_oauth("profile")
def rate_queries(task_id):
    """Api endpoint for rating GNQA query and answer"""
    with (require_oauth.acquire("profile") as token,
          db.connection(current_app.config["LLM_DB_PATH"]) as conn):
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
              task_id TEXT NOT NULL UNIQUE,
              created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY(task_id))"""
        cursor.execute(create_table)
        cursor.execute("""INSERT INTO Rating(user_id, query,
        answer, weight, task_id)
        VALUES(?, ?, ?, ?, ?)
        ON CONFLICT(task_id) DO UPDATE SET
        weight=excluded.weight
        """, (str(user_id), query, answer, weight, task_id))
        return {
           "message": "You have successfully rated this query. Thank you!"
        }, 200


@gnqa.route("/history", methods=["GET", "DELETE"])
@require_oauth("profile user")
def fetch_prev_history():
    """Api endpoint to fetch GNQA previous search."""
    with (require_oauth.acquire("profile user") as token,
          db.connection(current_app.config["LLM_DB_PATH"]) as conn):
        cursor = conn.cursor()
        if request.method == "DELETE":
            task_ids = list(request.json.values())
            query = """DELETE FROM history
            WHERE task_id IN ({})
            and user_id=?""".format(",".join("?" * len(task_ids)))
            cursor.execute(query, (*task_ids, str(token.user.user_id),))
            return jsonify({})
        elif (request.method == "GET" and
              request.args.get("search_term")):
            cursor.execute(
                """SELECT results from history
                Where task_id=? and user_id=?""",
                (request.args.get("search_term"),
                 str(token.user.user_id),))
            record = cursor.fetchone()
            if record:
                return dict(record).get("results")
            return {}
        cursor.execute(
            """SELECT task_id,query from history WHERE user_id=?""",
            (str(token.user.user_id),))
        return jsonify([dict(item) for item in cursor.fetchall()])
