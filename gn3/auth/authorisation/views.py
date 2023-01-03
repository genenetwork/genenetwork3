"""Endpoints for the authorisation stuff."""
from flask import jsonify, current_app

from gn3.auth import db
from .roles import user_roles as _user_roles
from ..authentication.oauth2.views import oauth2
from ..authentication.oauth2.resource_server import require_oauth

@oauth2.route("/user-roles")
@require_oauth
def user_roles():
    """Return the roles assigned to the user."""
    with require_oauth.acquire("role") as token:
        with db.connection(current_app.config["AUTH_DB"]) as conn:
            return jsonify(_user_roles(conn, token.user))
