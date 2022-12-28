"""Endpoints for the oauth2 server"""
import uuid

from flask import jsonify, Blueprint, current_app as app

from .resource_server import require_oauth
from .endpoints.revocation import RevocationEndpoint
from .endpoints.introspection import IntrospectionEndpoint

oauth2 = Blueprint("oauth2", __name__)

@oauth2.route("/register-client", methods=["GET", "POST"])
def register_client():
    """Register an OAuth2 client."""
    return "WOULD REGISTER ..."

@oauth2.route("/delete-client/<uuid:client_id>", methods=["GET", "POST"])
def delete_client(client_id: uuid.UUID):
    """Delete an OAuth2 client."""
    return f"WOULD DELETE OAUTH2 CLIENT {client_id}."

@oauth2.route("/authorise", methods=["GET", "POST"])
def authorise():
    """Authorise a user"""
    return "WOULD AUTHORISE THE USER."

@oauth2.route("/token", methods=["POST"])
def token():
    """Retrieve the authorisation token."""
    server = app.config["OAUTH2_SERVER"]
    return server.create_token_response()

@oauth2.route("/revoke", methods=["POST"])
def revoke_token():
    """Revoke the token."""
    return app.config["OAUTH2_SERVER"].create_endpoint_response(
        RevocationEndpoint.ENDPOINT_NAME)

@oauth2.route("/introspect", methods=["POST"])
def introspect_token():
    """Provide introspection information for the token."""
    return app.config["OAUTH2_SERVER"].create_endpoint_response(
        IntrospectionEndpoint.ENDPOINT_NAME)

@oauth2.route("/user")
@require_oauth("profile")
def user_details():
    with require_oauth.acquire("profile") as token:
        user = token.user
        return jsonify({
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name
        })
