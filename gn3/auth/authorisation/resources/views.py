"""The views/routes for the resources package"""
import uuid
import json
from functools import reduce

from flask import request, jsonify, Response, Blueprint, current_app as app

from gn3.auth.db_utils import with_db_connection

from .checks import authorised_for
from .models import (
    resource_by_id, resource_categories, link_data_to_resource,
    resource_category_by_id, unlink_data_from_resource,
    create_resource as _create_resource)

from ..roles import Role
from ..errors import InvalidData, AuthorisationError
from ..groups.models import Group, GroupRole, user_group, DUMMY_GROUP

from ... import db
from ...dictify import dictify
from ...authentication.users import User
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

@resources.route("/data/link", methods=["POST"])
@require_oauth("profile group resource")
def link_data():
    """Link group data to a specific resource."""
    try:
        form = request.form
        assert "resource_id" in form, "Resource ID not provided."
        assert "dataset_id" in form, "Dataset ID not provided."
        assert "dataset_type" in form, "Dataset type not specified"
        assert form["dataset_type"].lower() in (
            "mrna", "genotype", "phenotype"), "Invalid dataset type provided."

        with require_oauth.acquire("profile group resource") as the_token:
            def __link__(conn: db.DbConnection):
                return link_data_to_resource(
                    conn, the_token.user, uuid.UUID(form["resource_id"]),
                    form["dataset_type"], form["dataset_id"])

            return jsonify(with_db_connection(__link__))
    except AssertionError as aserr:
        raise InvalidData(aserr.args[0]) from aserr



@resources.route("/data/unlink", methods=["POST"])
@require_oauth("profile group resource")
def unlink_data():
    """Unlink data bound to a specific resource."""
    try:
        form = request.form
        assert "resource_id" in form, "Resource ID not provided."
        assert "dataset_id" in form, "Dataset ID not provided."

        with require_oauth.acquire("profile group resource") as the_token:
            def __unlink__(conn: db.DbConnection):
                return unlink_data_from_resource(
                    conn, the_token.user, uuid.UUID(form["resource_id"]),
                    form["dataset_id"])
            return jsonify(with_db_connection(__unlink__))
    except AssertionError as aserr:
        raise InvalidData(aserr.args[0]) from aserr

@resources.route("<uuid:resource_id>/users", methods=["GET"])
@require_oauth("profile group resource")
def resource_users(resource_id: uuid.UUID):
    """Retrieve all users with access to the given resource."""
    with require_oauth.acquire("profile group resource") as the_token:
        def __the_users__(conn: db.DbConnection):
            authorised = authorised_for(
                conn, the_token.user, ("group:resource:edit-resource",),
                (resource_id,))
            if authorised.get(resource_id, False):
                with db.cursor(conn) as cursor:
                    group = user_group(cursor, the_token.user).maybe(
                        DUMMY_GROUP, lambda grp: grp)
                    if group == DUMMY_GROUP:
                        raise AuthorisationError(
                            "Users who are not members of groups cannot access "
                            "resource details.")
                    def __organise_users_n_roles__(users_n_roles, row):
                        user_id = uuid.UUID(row["user_id"])
                        user = users_n_roles.get(
                            user_id, User(user_id, row["email"], row["name"]))
                        role = GroupRole(
                            uuid.UUID(row["group_role_id"]),
                            group,
                            Role(uuid.UUID(row["role_id"]), row["role_name"],
                                 tuple()))
                        return {
                            **users_n_roles,
                            user_id: {
                                "user": user,
                                "user_group": Group(
                                    uuid.UUID(row["group_id"]), row["group_name"],
                                    json.loads(row["group_metadata"])),
                                "roles": users_n_roles.get(
                                    user_id, {}).get("roles", tuple()) + (role,)
                            }
                        }
                    cursor.execute(
                        "SELECT g.*, u.*, r.*, gr.group_role_id "
                        "FROM groups AS g INNER JOIN "
                        "group_users AS gu ON g.group_id=gu.group_id "
                        "INNER JOIN users AS u ON gu.user_id=u.user_id "
                        "INNER JOIN group_user_roles_on_resources AS guror "
                        "ON u.user_id=guror.user_id INNER JOIN roles AS r "
                        "ON guror.role_id=r.role_id "
                        "INNER JOIN group_roles AS gr ON r.role_id=gr.role_id "
                        "WHERE guror.resource_id=?",
                        (str(resource_id),))
                    return reduce(__organise_users_n_roles__, cursor.fetchall(), {})
            raise AuthorisationError(
                "You do not have sufficient privileges to view the resource "
                "users.")
        results = (
            {
                "user": dictify(row["user"]),
                "user_group": dictify(row["user_group"]),
                "roles": tuple(dictify(role) for role in row["roles"])
            } for row in (
                user_row for user_id, user_row
                in with_db_connection(__the_users__).items()))
        return jsonify(tuple(results))
