"""Endpoints for the authorisation stuff."""
from flask import jsonify, current_app

from gn3.auth import db
from .groups import user_group
from .roles import user_roles as _user_roles
from ..authentication.oauth2.views import oauth2
from ..authentication.oauth2.resource_server import require_oauth

@oauth2.route("/user")
@require_oauth("profile")
def user_details():
    """Return user's details."""
    with require_oauth.acquire("profile") as the_token:
        user = the_token.user
        with db.connection(current_app.config["AUTH_DB"]) as conn, db.cursor(conn) as cursor:
            group = user_group(cursor, user)

        return jsonify({
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "group": group.maybe(False, lambda grp: grp)
        })

@oauth2.route("/user-roles")
@require_oauth
def user_roles():
    """Return the non-resource roles assigned to the user."""
    with require_oauth.acquire("role") as token:
        with db.connection(current_app.config["AUTH_DB"]) as conn:
            return jsonify(_user_roles(conn, token.user))
