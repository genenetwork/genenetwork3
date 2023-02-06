"""The views/routes for the resources package"""
import uuid
from flask import request, jsonify, Response, Blueprint, current_app as app

from .models import (
    resource_by_id, resource_categories, resource_category_by_id,
    create_resource as _create_resource)

from ... import db
from ...dictify import dictify
from ...authentication.oauth2.resource_server import require_oauth

resources = Blueprint("resources", __name__)

@resources.route("/categories", methods=["GET"])
@require_oauth("profile group resource")
def list_resource_categories() -> Response:
    """Retrieve all resource categories"""
    db_uri = app.config["AUTH_DB"]
    with db.connection(db_uri) as conn:
        return jsonify(tuple(
            dictify(category) for category in resource_categories(conn)))

@resources.route("/create", methods=["POST"])
@require_oauth("profile group resource")
def create_resource() -> Response:
    """Create a new resource"""
    with require_oauth.acquire("profile group resource") as the_token:
        form = request.form
        resource_name = form.get("resource_name")
        resource_category_id = uuid.UUID(form.get("resource_category"))
        db_uri = app.config["AUTH_DB"]
        with db.connection(db_uri) as conn:
            resource = _create_resource(
                conn, resource_name, resource_category_by_id(
                    conn, resource_category_id),
                the_token.user)
            return jsonify(dictify(resource))

@resources.route("/view/<uuid:resource_id>")
@require_oauth("profile group resource")
def view_resource(resource_id: uuid.UUID) -> Response:
    """View a particular resource's details."""
    with require_oauth.acquire("profile group resource") as the_token:
        db_uri = app.config["AUTH_DB"]
        with db.connection(db_uri) as conn:
            return jsonify(dictify(resource_by_id(
                conn, the_token.user, resource_id)))
