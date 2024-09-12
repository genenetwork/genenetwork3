"""Api endpoints for gnqa"""
import json
from datetime import datetime

from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.llms.process import get_gnqa
from gn3.llms.errors import LLMError
from gn3.auth.authorisation.oauth2.resource_server import require_oauth
from gn3.auth import db


gnqa = Blueprint("gnqa", __name__)

HISTORY_TABLE_CREATE_QUERY = """
CREATE TABLE IF NOT EXISTS history(
    user_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    query TEXT NOT NULL,
    results JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(task_id)
    ) WITHOUT ROWID
"""

RATING_TABLE_CREATE_QUERY = """
CREATE TABLE IF NOT EXISTS Rating(
    user_id TEXT NOT NULL,
    query TEXT NOT NULL,
    answer TEXT NOT NULL,
    weight INTEGER NOT NULL DEFAULT 0,
    task_id TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(task_id)
    )
"""


def database_setup():
    """Temporary method to remove the need to have CREATE queries in functions"""
    with db.connection(current_app.config["LLM_DB_PATH"]) as conn:
        cursor = conn.cursor()
        cursor.execute(HISTORY_TABLE_CREATE_QUERY)
        cursor.execute(RATING_TABLE_CREATE_QUERY)


@gnqa.route("/search", methods=["GET"])
def search():
    """Api  endpoint for searching queries in fahamu Api"""
    query = request.args.get("query", "")
    if not query:
        return jsonify({"error": "query get parameter is missing in the request"}), 400
    fahamu_token = current_app.config.get("FAHAMU_AUTH_TOKEN")
    if not fahamu_token:
        raise LLMError(
            "Request failed: an LLM authorisation token  is required ", query)
    database_setup()
    with (db.connection(current_app.config["LLM_DB_PATH"]) as conn,
          require_oauth.acquire("profile user") as token):
        cursor = conn.cursor()
        previous_answer_query = """
        SELECT user_id, task_id, query, results FROM history
            WHERE created_at > DATE('now', '-1 day') AND
                user_id = ? AND
                query = ?
            ORDER BY created_at DESC LIMIT 1 """
        res = cursor.execute(previous_answer_query, (str(token.user.user_id), query))
        previous_result = res.fetchone()
        if previous_result:
            _, _, _, response = previous_result
            return response

        task_id, answer, refs = get_gnqa(
            query, fahamu_token, current_app.config.get("DATA_DIR"))
        response = {
            "task_id": task_id,
            "query": query,
            "answer": answer,
            "references": refs
        }
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
    database_setup()
    with (require_oauth.acquire("profile") as token,
          db.connection(current_app.config["LLM_DB_PATH"]) as conn):
        results = request.json
        user_id, query, answer, weight = (token.user.user_id,
                                          results.get("query"),
                                          results.get("answer"),
                                          results.get("weight", 0))
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO Rating(user_id, query,
        answer, weight, task_id)
        VALUES(?, ?, ?, ?, ?)
        ON CONFLICT(task_id) DO UPDATE SET
        weight=excluded.weight
        """, (str(user_id), query, answer, weight, task_id))
        return {
            "message": "You have successfully rated this query. Thank you!"
        }, 200


@gnqa.route("/search/records", methods=["GET"])
@require_oauth("profile user")
def get_user_search_records():
    """get all  history records for a given user using their
    user id
    """
    with (require_oauth.acquire("profile user") as token,
          db.connection(current_app.config["LLM_DB_PATH"]) as conn):
        cursor = conn.cursor()
        cursor.execute(
            """SELECT task_id, query, created_at from history WHERE user_id=?""",
            (str(token.user.user_id),))
        results = [dict(item) for item in cursor.fetchall()]
        return jsonify(sorted(results, reverse=True,
                              key=lambda x: datetime.strptime(x.get("created_at"),
                                                              '%Y-%m-%d %H:%M:%S')))


@gnqa.route("/search/record/<task_id>", methods=["GET"])
@require_oauth("profile user")
def get_user_record_by_task(task_id):
    """Get user previous search record by task id """
    with (require_oauth.acquire("profile user") as token,
          db.connection(current_app.config["LLM_DB_PATH"]) as conn):
        cursor = conn.cursor()
        cursor.execute(
            """SELECT results from history
            Where task_id=? and user_id=?""",
            (task_id,
             str(token.user.user_id),))
        record = cursor.fetchone()
        if record:
            return dict(record).get("results")
        return {}


@gnqa.route("/search/record/<task_id>", methods=["DELETE"])
@require_oauth("profile user")
def delete_record(task_id):
    """Delete user previous seach record by task-id"""
    with (require_oauth.acquire("profile user") as token,
          db.connection(current_app.config["LLM_DB_PATH"]) as conn):
        cursor = conn.cursor()
        query = """DELETE FROM history
        WHERE task_id=? and user_id=?"""
        cursor.execute(query, (task_id, token.user.user_id,))
        return {"msg": f"Successfully Deleted the task {task_id}"}


@gnqa.route("/search/records", methods=["DELETE"])
@require_oauth("profile user")
def delete_records():
    """ Delete a users records using for all given task ids"""
    with (require_oauth.acquire("profile user") as token,
          db.connection(current_app.config["LLM_DB_PATH"]) as conn):
        task_ids = list(request.json.values())
        cursor = conn.cursor()
        query = f"""
DELETE FROM history WHERE task_id IN ({', '.join('?' * len(task_ids))}) AND user_id=?
        """
        cursor.execute(query, (*task_ids, str(token.user.user_id),))
        return jsonify({})
