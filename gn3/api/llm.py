"""Api endpoints for gnqa"""
import ipaddress
import json
import string
import uuid

from datetime import datetime
from datetime import timedelta
from typing import Optional
from functools import wraps

from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import request

from authlib.jose.errors import DecodeError
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


RATE_LIMITER_TABLE_CREATE_QUERY = """
CREATE TABLE IF NOT EXISTS Limiter(
    identifier TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tokens INTEGER,
    expiry_time TIMESTAMP,
    PRIMARY KEY(identifier)
)
"""


def database_setup():
    """Temporary method to remove the need to have CREATE queries in functions"""
    with db.connection(current_app.config["LLM_DB_PATH"]) as conn:
        cursor = conn.cursor()
        cursor.execute(HISTORY_TABLE_CREATE_QUERY)
        cursor.execute(RATING_TABLE_CREATE_QUERY)
        cursor.execute(RATE_LIMITER_TABLE_CREATE_QUERY)


def clean_query(query:str) -> str:
    """This function cleans up query  removing
    punctuation  and whitepace and transform to
    lowercase
    clean_query("!hello test.") -> "hello test"
    """
    strip_chars = string.punctuation + string.whitespace
    str_query = query.lower().strip(strip_chars)
    return str_query


def is_verified_anonymous_user(request_metadata):
    """This function should verify autheniticity of metadate from gn2 """
    anony_id = request_metadata.headers.get("Anonymous-Id") #should verify this + metadata signature
    user_status = request_metadata.headers.get("Anonymous-Status", "")
    _user_signed_metadata = (
        request_metadata.headers.get("Anony-Metadata", "")) # TODO~ verify this for integrity
    return bool(anony_id) and user_status.lower() == "verified"

def with_gnqna_fallback(view_func):
    """Allow fallback to GNQNA user if token auth fails or token is malformed."""
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        def call_with_anonymous_fallback():
            return view_func.__wrapped__(*args,
                   **{**kwargs, "auth_token": None, "valid_anony": True})

        try:
            response = view_func(*args, **kwargs)

            is_invalid_token = (
                isinstance(response, tuple) and
                len(response) == 2 and
                response[1] == 400
            )

            if is_invalid_token and is_verified_anonymous_user(request):
                return call_with_anonymous_fallback()

            return response

        except (DecodeError, ValueError): # occurs when trying to parse the token or auth results
            if is_verified_anonymous_user(request):
                return call_with_anonymous_fallback()
            return view_func.__wrapped__(*args, **kwargs)

    return wrapper


def is_valid_address(ip_string) -> bool :
    """Function checks if is a valid ip address is valid"""
    # todo !verify data is sent from gn2
    try:
        ipaddress.ip_address(ip_string)
        return True
    except ValueError:
        return False


def check_rate_limiter(request_metadata, db_path, tokens_lifespan=1440, default_tokens=4):
    """
    Checks if an anonymous user has a valid token within the given lifespan.
    If expired or not found, creates or resets the token bucket.
    `tokens_lifespan` is in seconds.  24*60
    default_token set to 4 requests per hour.
    """
    # Extract IP address /identifier
    user_metadata = json.loads(request_metadata.headers.get("Anony-Metadata", {}))
    ip_address = user_metadata.get("ip_address")
    if not ip_address or not is_valid_address(ip_address):
        raise ValueError("Please provide a valid IP address")
    now = datetime.utcnow()
    new_expiry = (now + timedelta(seconds=tokens_lifespan)).strftime("%Y-%m-%d %H:%M:%S")

    with  db.connection(db_path) as conn:
        cursor = conn.cursor()
        # Fetch existing limiter record
        cursor.execute("""
            SELECT tokens, expiry_time FROM Limiter
            WHERE identifier = ?
        """, (ip_address,))
        row = cursor.fetchone()

        if row:
            tokens, expiry_time_str = row
            expiry_time = datetime.strptime(expiry_time_str, "%Y-%m-%d %H:%M:%S")
            time_diff = (expiry_time - now).total_seconds()

            if 0 < time_diff <= tokens_lifespan:
                if tokens > 0:
                    # Consume token
                    cursor.execute("""
                        UPDATE Limiter
                        SET tokens = tokens - 1
                        WHERE identifier = ? AND tokens > 0
                    """, (ip_address,))
                    return True
                else:
                    raise LLMError("Rate limit exceeded. Please try again later.",
                                   request_metadata.args.get("query"))
            else:
                # Token expired — reset ~probably reset this after 200 status
                cursor.execute("""
                    UPDATE Limiter
                    SET tokens = ?, expiry_time = ?
                    WHERE identifier = ?
                """, (default_tokens, new_expiry, ip_address))
                return True
        else:
            # New user — insert record  ~probably reset this after 200 status
            cursor.execute("""
                INSERT INTO Limiter(identifier, tokens, expiry_time)
                VALUES (?, ?, ?)
            """, (ip_address, default_tokens, new_expiry))
            return True


@gnqa.route("/search", methods=["GET"])
@with_gnqna_fallback
@require_token
def search(auth_token=None, valid_anony=False):
    """Api  endpoint for searching queries in fahamu Api"""
    query = request.args.get("query", "")
    if not query:
        return jsonify({"error": "query get parameter is missing in the request"}), 400

    fahamu_token = current_app.config.get("FAHAMU_AUTH_TOKEN")
    if not fahamu_token:
        raise LLMError(
            "Request failed: an LLM authorisation token  is required ", query)
    database_setup()
    # check if is valid anon
    # if valid_anony:
    check_rate_limiter(request, current_app.config["LLM_DB_PATH"]) #Will raise error if not
    # else verified user allowed
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
            response = json.loads(response)
            response["query"] = query
            return response

        if valid_anony:
            # rate limit anonymous verified users
            check_rate_limiter(request, current_app.config["LLM_DB_PATH"])

        task_id, answer, refs = get_gnqa(
            query, fahamu_token, current_app.config.get("DATA_DIR"))
        response = {
            "task_id": task_id,
            "query": query,
            "answer": answer,
            "references": refs
        }
        user_id = str(uuid.uuid4()) if valid_anony else get_user_id(auth_token)
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
