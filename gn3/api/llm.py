"""Api endpoints for gnqa"""
import json
import string
from datetime import datetime
from typing import Optional

from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from gn3.llms.process import get_gnqa
from gn3.llms.errors import LLMError

from gn3.oauth2.authorisation import require_token
from gn3 import sqlite_db_utils as db


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


def clean_query(query:str) -> str:
    """This function cleans up query  removing
    punctuation  and whitepace and transform to
    lowercase
    clean_query("!hello test.") -> "hello test"
    """
    strip_chars = string.punctuation + string.whitespace
    str_query = query.lower().strip(strip_chars)
    return str_query

@gnqa.route("/search", methods=["GET"])
@require_token
def search(auth_token=None):
    """Api  endpoint for searching queries in fahamu Api"""
    query = request.args.get("query", "")
    if not query:
        return jsonify({"error": "query get parameter is missing in the request"}), 400
    fahamu_token = current_app.config.get("FAHAMU_AUTH_TOKEN")
    if not fahamu_token:
        raise LLMError(
            "Request failed: an LLM authorisation token  is required ", query)
    database_setup()
    with db.connection(current_app.config["LLM_DB_PATH"]) as conn:
        cursor = conn.cursor()
        previous_answer_query = """
        SELECT user_id, task_id, query, results FROM history
            WHERE created_at > DATE('now', '-21 day') AND
                query = ?
            ORDER BY created_at DESC LIMIT 1 """
        res = cursor.execute(previous_answer_query, (clean_query(query),))
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
        user_id = get_user_id(auth_token)
        cursor.execute(
            """INSERT INTO history(user_id, task_id, query, results)
            VALUES(?, ?, ?, ?)
            """, (user_id, str(task_id["task_id"]),
                  clean_query(query),
                  json.dumps(response))
        )
        return response


@gnqa.route("/rating/<task_id>", methods=["POST"])
@require_token
def rate_queries(task_id, auth_token=None):
    """Api endpoint for rating GNQA query and answer"""
    database_setup()
    user_id = get_user_id(auth_token)
    with db.connection(current_app.config["LLM_DB_PATH"]) as conn:
        results = request.json
        query, answer, weight = (results.get("query"),
                                 results.get("answer"),
                                 results.get("weight", 0))
        cursor = conn.cursor()
        cursor.execute("""INSERT INTO Rating(user_id, query,
        answer, weight, task_id)
        VALUES(?, ?, ?, ?, ?)
        ON CONFLICT(task_id) DO UPDATE SET
        weight=excluded.weight
        """, (user_id, query, answer, weight, task_id))
        return {
            "message": "You have successfully rated this query. Thank you!"
        }, 200


@gnqa.route("/search/records", methods=["GET"])
@require_token
def get_user_search_records(auth_token=None):
    """get all  history records for a given user using their
    user id
    """
    with db.connection(current_app.config["LLM_DB_PATH"]) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT task_id, query, created_at from history WHERE user_id=?""",
            (get_user_id(auth_token),))
        results = [dict(item) for item in cursor.fetchall()]
        return jsonify(sorted(results, reverse=True,
                              key=lambda x: datetime.strptime(x.get("created_at"),
                                                              '%Y-%m-%d %H:%M:%S')))


@gnqa.route("/search/record/<task_id>", methods=["GET"])
@require_token
def get_user_record_by_task(task_id, auth_token = None):
    """Get user previous search record by task id """
    with db.connection(current_app.config["LLM_DB_PATH"]) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT results from history
            Where task_id=? and user_id=?""",
            (task_id, get_user_id(auth_token),))
        record = cursor.fetchone()
        if record:
            return dict(record).get("results")
        return {}


@gnqa.route("/search/record/<task_id>", methods=["DELETE"])
@require_token
def delete_record(task_id, auth_token = None):
    """Delete user previous seach record by task-id"""
    with db.connection(current_app.config["LLM_DB_PATH"]) as conn:
        cursor = conn.cursor()
        query = """DELETE FROM history
        WHERE task_id=? and user_id=?"""
        cursor.execute(query, (task_id, get_user_id(auth_token),))
        return {"msg": f"Successfully Deleted the task {task_id}"}


@gnqa.route("/search/records", methods=["DELETE"])
@require_token
def delete_records(auth_token=None):
    """ Delete a users records using for all given task ids"""
    with db.connection(current_app.config["LLM_DB_PATH"]) as conn:
        task_ids = list(request.json.values())
        cursor = conn.cursor()
        query = ("DELETE FROM history WHERE task_id IN "
                 f"({', '.join('?' * len(task_ids))}) "
                 "AND user_id=?")
        cursor.execute(query, (*task_ids, get_user_id(auth_token),))
        return jsonify({})


def get_user_id(auth_token: Optional[dict] = None):
    """Retrieve the user ID from the JWT token."""
    if auth_token is None or auth_token.get("jwt", {}).get("sub") is None:
        raise LLMError("Invalid auth token encountered")
    user_id = auth_token["jwt"]["sub"]
    return user_id
