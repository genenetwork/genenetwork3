"""The views/routes for the `gn3.auth.authorisation.groups` package."""
import uuid

from flask import request, jsonify, Response, Blueprint, current_app

from gn3.auth import db
from gn3.auth.dictify import dictify

from .models import (
    all_groups, GroupCreationError, group_users as _group_users,
    create_group as _create_group)

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
