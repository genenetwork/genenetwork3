"""The views/routes for the `gn3.auth.authorisation.roles` package."""
import uuid

from flask import jsonify, Response, Blueprint, current_app

from gn3.auth import db
from gn3.auth.dictify import dictify

from .models import user_role

from ...authentication.oauth2.resource_server import require_oauth

roles = Blueprint("roles", __name__)

@roles.route("/view/<uuid:role_id>", methods=["GET"])
@require_oauth("profile role")
def view_role(role_id: uuid.UUID) -> Response:
    """Retrieve a user role with id `role_id`"""
    def __error__(exc: Exception):
        raise exc
    with require_oauth.acquire("profile role") as the_token:
        db_uri = current_app.config["AUTH_DB"]
        with db.connection(db_uri) as conn:
            the_role = user_role(conn, the_token.user, role_id)
            return the_role.either(
                __error__, lambda a_role: jsonify(dictify(a_role)))
