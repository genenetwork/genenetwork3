"""The views/routes for the resources package"""
import uuid
from flask import request, jsonify, Response, Blueprint, current_app as app

from .models import (
    resource_by_id, resource_categories, resource_category_by_id,
    create_resource as _create_resource)

from ..groups.models import user_group, DUMMY_GROUP

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

@resources.route("/<string:resource_type>/unlinked-data")
@require_oauth("profile group resource")
def unlinked_data(resource_type: str) -> Response:
    """View unlinked data"""
    with require_oauth.acquire("profile group resource") as the_token:
        db_uri = app.config["AUTH_DB"]
        with db.connection(db_uri) as conn, db.cursor(conn) as cursor:
            ugroup = user_group(cursor, the_token.user).maybe(# type: ignore[misc]
                DUMMY_GROUP, lambda grp: grp)
            if ugroup == DUMMY_GROUP:
                return jsonify(tuple())
            type_filter = {
                "all": "",
                "mrna": 'WHERE dataset_type="mRNA"',
                "genotype": 'WHERE dataset_type="Genotype"',
                "phenotype": 'WHERE dataset_type="Phenotype"'
            }[resource_type]

            except_filter = (
                "SELECT group_id, dataset_type, "
                "dataset_id AS dataset_or_trait_id FROM mrna_resources "
                "UNION "
                "SELECT group_id, dataset_type, "
                "trait_id AS dataset_or_trait_id FROM genotype_resources "
                "UNION "
                "SELECT group_id, dataset_type, "
                "trait_id AS dataset_or_trait_id FROM phenotype_resources")

            ids_query = ("SELECT group_id, dataset_type, dataset_or_trait_id "
                         "FROM linked_group_data "
                         f"{type_filter} "
                         f"EXCEPT {except_filter} ")
            cursor.execute(ids_query)
            ids = cursor.fetchall()

            if ids:
                clause = ", ".join(["(?, ?, ?)"] * len(ids))
                data_query = (
                    "SELECT * FROM linked_group_data "
                    "WHERE (group_id, dataset_type, dataset_or_trait_id) "
                    f"IN (VALUES {clause})")
                params = tuple(item for sublist in
                               ((row[0], row[1], row[2]) for row in ids)
                               for item in sublist)
                cursor.execute(data_query, params)
                return jsonify(tuple(dict(row) for row in cursor.fetchall()))

    return jsonify(tuple())
