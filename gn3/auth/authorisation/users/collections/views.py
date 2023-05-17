"""Views regarding user collections."""
from uuid import UUID

from redis import Redis
from flask import jsonify, request, Response, Blueprint, current_app

from gn3.auth import db
from gn3.auth.db_utils import with_db_connection
from gn3.auth.authorisation.checks import require_json
from gn3.auth.authorisation.errors import NotFoundError

from gn3.auth.authentication.users import User, user_by_id
from gn3.auth.authentication.oauth2.resource_server import require_oauth

from .models import (
    get_collection, user_collections, save_collections, create_collection,
    delete_collections as _delete_collections)

collections = Blueprint("collections", __name__)

@collections.route("/list")
@require_oauth("profile user")
def list_user_collections() -> Response:
    """Retrieve the user ids"""
    with (require_oauth.acquire("profile user") as the_token,
          Redis.from_url(current_app.config["REDIS_URI"],
                         decode_responses=True) as redisconn):
        return jsonify(user_collections(redisconn, the_token.user))

@collections.route("/<uuid:anon_id>/list")
def list_anonymous_collections(anon_id: UUID) -> Response:
    """Fetch anonymous collections"""
    with Redis.from_url(
            current_app.config["REDIS_URI"], decode_responses=True) as redisconn:
        def __list__(conn: db.DbConnection) -> tuple:
            try:
                _user = user_by_id(conn, anon_id)
                current_app.logger.warning(
                    "Fetch collections for authenticated user using the "
                    "`list_user_collections()` endpoint.")
                return tuple()
            except NotFoundError as _nfe:
                return user_collections(
                    redisconn, User(anon_id, "anon@ymous.user", "Anonymous User"))

        return jsonify(with_db_connection(__list__))

@require_oauth("profile user")
def __new_collection_as_authenticated_user__(redisconn, name, traits):
    """Create a new collection as an authenticated user."""
    with require_oauth.acquire("profile user") as token:
        return create_collection(redisconn, token.user, name, traits)

def __new_collection_as_anonymous_user__(redisconn, name, traits):
    """Create a new collection as an anonymous user."""
    return create_collection(redisconn,
                             User(UUID(request.json.get("anon_id")),
                                  "anon@ymous.user",
                                  "Anonymous User"),
                             name,
                             traits)

@collections.route("/new", methods=["POST"])
@require_json
def new_user_collection() -> Response:
    """Create a new collection."""
    with (Redis.from_url(current_app.config["REDIS_URI"],
                         decode_responses=True) as redisconn):
        traits = tuple(request.json.get("traits", tuple()))# type: ignore[union-attr]
        name = request.json.get("name")# type: ignore[union-attr]
        if bool(request.headers.get("Authorization")):
            return jsonify(__new_collection_as_authenticated_user__(
                redisconn, name, traits))
        return jsonify(__new_collection_as_anonymous_user__(
            redisconn, name, traits))

@collections.route("/<uuid:collection_id>/view", methods=["POST"])
@require_json
def view_collection(collection_id: UUID) -> Response:
    """View a particular collection"""
    with (Redis.from_url(current_app.config["REDIS_URI"],
                         decode_responses=True) as redisconn):
        if bool(request.headers.get("Authorization")):
            with require_oauth.acquire("profile user") as token:
                return jsonify(get_collection(redisconn,
                                              token.user,
                                              collection_id))
        return jsonify(get_collection(
            redisconn,
            User(
                UUID(request.json.get("anon_id")),#type: ignore[union-attr]
                "anon@ymous.user",
                "Anonymous User"),
            collection_id))

@collections.route("/anonymous/import", methods=["POST"])
@require_json
@require_oauth("profile user")
def import_anonymous() -> Response:
    """Import anonymous collections."""
    with (require_oauth.acquire("profile user") as token,
          Redis.from_url(current_app.config["REDIS_URI"],
                         decode_responses=True) as redisconn):
        anon_id = UUID(request.json.get("anon_id"))#type: ignore[union-attr]
        anon_colls = user_collections(redisconn, User(
            anon_id, "anon@ymous.user", "Anonymous User"))
        save_collections(
            redisconn,
            token.user,
            (user_collections(redisconn, token.user) +
             anon_colls))
        redisconn.hdel("collections", str(anon_id))
        return jsonify({
            "message": f"Import of {len(anon_colls)} was successful."
        })

@collections.route("/anonymous/delete", methods=["POST"])
@require_json
@require_oauth("profile user")
def delete_anonymous() -> Response:
    """Delete anonymous collections."""
    with (require_oauth.acquire("profile user") as _token,
          Redis.from_url(current_app.config["REDIS_URI"],
                         decode_responses=True) as redisconn):
        anon_id = UUID(request.json.get("anon_id"))#type: ignore[union-attr]
        anon_colls = user_collections(redisconn, User(
            anon_id, "anon@ymous.user", "Anonymous User"))
        redisconn.hdel("collections", str(anon_id))
        return jsonify({
            "message": f"Deletion of {len(anon_colls)} was successful."
        })

@collections.route("/delete", methods=["POST"])
@require_json
def delete_collections():
    """Delete specified collections."""
    with (Redis.from_url(current_app.config["REDIS_URI"],
                         decode_responses=True) as redisconn):
        coll_ids = tuple(UUID(cid) for cid in request.json["collection_ids"])
        deleted = _delete_collections(
            redisconn,
            User(request.json["anon_id"], "anon@ymous.user", "Anonymous User"),
            coll_ids)
        if bool(request.headers.get("Authorization")):
            with require_oauth.acquire("profile user") as token:
                deleted = deleted + _delete_collections(
                    redisconn, token.user, coll_ids)

        return jsonify({
            "message": f"Deleted {len(deleted)} collections."})
