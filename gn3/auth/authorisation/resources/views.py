"""The views/routes for the resources package"""
import uuid
from functools import partial

from flask import request, jsonify, Response, Blueprint, current_app as app

from gn3 import db_utils as gn3dbutils
from gn3.auth.db_utils import with_db_connection

from .data import link_data_to_group, retrieve_ungrouped_data
from .models import (
    resource_by_id, resource_categories, resource_category_by_id,
    create_resource as _create_resource)

from ..errors import InvalidData, AuthorisationError
from ..groups.models import user_group, DUMMY_GROUP, group_by_id

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
    """View data linked to the group but not linked to any resource."""
    if resource_type not in ("all", "mrna", "genotype", "phenotype"):
        raise AuthorisationError(f"Invalid resource type {resource_type}")

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

@resources.route("/<string:dataset_type>/ungrouped-data", methods=["GET"])
@require_oauth("profile group resource")
def ungrouped_data(dataset_type: str) -> Response:
    """View data not linked to any group."""
    if dataset_type not in ("all", "mrna", "genotype", "phenotype"):
        raise AuthorisationError(f"Invalid dataset type {dataset_type}")

    with require_oauth.acquire("profile group resource") as _the_token:
        with gn3dbutils.database_connection() as gn3conn:
            return jsonify(with_db_connection(partial(
                retrieve_ungrouped_data, gn3conn=gn3conn,
                dataset_type=dataset_type)))

@resources.route("/data/link", methods=["POST"])
@require_oauth("profile group resource")
def link_data() -> Response:
    """Link selected data to specified group."""
    with require_oauth.acquire("profile group resource") as _the_token:
        form = request.form
        group_id = uuid.UUID(form["group_id"])
        dataset_id = form["dataset_id"]
        dataset_type = form.get("dataset_type")
        if dataset_type not in ("mrna", "genotype", "phenotype"):
            raise InvalidData("Unexpected dataset type requested!")
        def __link__(conn: db.DbConnection):
            group = group_by_id(conn, group_id)
            with gn3dbutils.database_connection() as gn3conn:
                return link_data_to_group(
                    conn, gn3conn, dataset_type, dataset_id, group)

        return jsonify(with_db_connection(__link__))
