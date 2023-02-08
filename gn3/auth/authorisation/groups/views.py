"""The views/routes for the `gn3.auth.authorisation.groups` package."""
import uuid
import datetime
from functools import partial

from flask import request, jsonify, Response, Blueprint, current_app

from gn3.auth import db
from gn3.auth.dictify import dictify
from gn3.auth.db_utils import with_db_connection

from .models import (
    user_group, all_groups, join_requests, accept_join_request,
    GroupCreationError, group_users as _group_users,
    create_group as _create_group)

from ..errors import AuthorisationError

from ...authentication.users import User
from ...authentication.oauth2.resource_server import require_oauth

groups = Blueprint("groups", __name__)

@groups.route("/list", methods=["GET"])
@require_oauth("profile group")
def list_groups():
    """Return the list of groups that exist."""
    with db.connection(current_app.config["AUTH_DB"]) as conn:
        the_groups = all_groups(conn)

    return jsonify(the_groups.maybe(
        [], lambda grps: [dictify(grp) for grp in grps]))

@groups.route("/create", methods=["POST"])
@require_oauth("profile group")
def create_group():
    """Create a new group."""
    with require_oauth.acquire("profile group") as the_token:
        group_name=request.form.get("group_name", "").strip()
        if not bool(group_name):
            raise GroupCreationError("Could not create the group.")

        db_uri = current_app.config["AUTH_DB"]
        with db.connection(db_uri) as conn:
            user = the_token.user
            new_group = _create_group(
                conn, group_name, user, request.form.get("group_description"))
            return jsonify({
                **dictify(new_group), "group_leader": dictify(user)
            })

@groups.route("/members/<uuid:group_id>", methods=["GET"])
@require_oauth("profile group")
def group_members(group_id: uuid.UUID) -> Response:
    """Retrieve all the members of a group."""
    with require_oauth.acquire("profile group") as the_token:# pylint: disable=[unused-variable]
        db_uri = current_app.config["AUTH_DB"]
        ## Check that user has appropriate privileges and remove the pylint disable above
        with db.connection(db_uri) as conn:
            return jsonify(tuple(
                dictify(user) for user in _group_users(conn, group_id)))

@groups.route("/requests/join/<uuid:group_id>", methods=["POST"])
@require_oauth("profile group")
def request_to_join(group_id: uuid.UUID) -> Response:
    """Request to join a group."""
    def __request__(conn: db.DbConnection, user: User, group_id: uuid.UUID,
                    message: str):
        with db.cursor(conn) as cursor:
            group = user_group(cursor, user).maybe(# type: ignore[misc]
                False, lambda grp: grp)# type: ignore[arg-type]
            if group:
                error = AuthorisationError(
                    "You cannot request to join a new group while being a "
                    "member of an existing group.")
                error.error_code = 400
                raise error
            request_id = uuid.uuid4()
            cursor.execute(
                "INSERT INTO group_join_requests VALUES "
                "(:request_id, :group_id, :user_id, :ts, :status, :msg)",
                {
                    "request_id": str(request_id),
                    "group_id": str(group_id),
                    "user_id": str(user.user_id),
                    "ts": datetime.datetime.now().timestamp(),
                    "status": "PENDING",
                    "msg": message
                })
            return {
                "request_id":  request_id,
                "message": "Successfully sent the join request."
            }

    with require_oauth.acquire("profile group") as the_token:
        form = request.form
        results = with_db_connection(partial(
            __request__, user=the_token.user, group_id=group_id, message=form.get(
                "message", "I hereby request that you add me to your group.")))
        return jsonify(results)

@groups.route("/requests/join/list", methods=["GET"])
@require_oauth("profile group")
def list_join_requests() -> Response:
    """List the pending join requests."""
    with require_oauth.acquire("profile group") as the_token:
        return jsonify(with_db_connection(partial(
            join_requests, user=the_token.user)))

@groups.route("/requests/join/accept", methods=["POST"])
@require_oauth("profile group")
def accept_join_requests() -> Response:
    """Accept a join request."""
    with require_oauth.acquire("profile group") as the_token:
        form = request.form
        request_id = uuid.UUID(form.get("request_id"))
        return jsonify(with_db_connection(partial(
            accept_join_request, request_id=request_id, user=the_token.user)))
