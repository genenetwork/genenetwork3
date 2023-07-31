"""The views/routes for the resources package"""
import uuid
import json
import sqlite3
from functools import reduce

from flask import request, jsonify, Response, Blueprint, current_app as app

from gn3.auth.db_utils import with_db_connection

from .checks import authorised_for
from .models import (
    Resource, save_resource, resource_data, resource_by_id, resource_categories,
    assign_resource_user, link_data_to_resource, unassign_resource_user,
    resource_category_by_id, unlink_data_from_resource,
    create_resource as _create_resource)

from ..roles import Role
from ..errors import InvalidData, InconsistencyError, AuthorisationError
from ..groups.models import Group, GroupRole, group_role_by_id

from ... import db
from ...dictify import dictify
from ...authentication.oauth2.resource_server import require_oauth
from ...authentication.users import User, user_by_id, user_by_email

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
            try:
                resource = _create_resource(
                    conn,
                    resource_name,
                    resource_category_by_id(conn, resource_category_id),
                    the_token.user,
                    (form.get("public") == "on"))
                return jsonify(dictify(resource))
            except sqlite3.IntegrityError as sql3ie:
                if sql3ie.args[0] == ("UNIQUE constraint failed: "
                                      "resources.resource_name"):
                    raise InconsistencyError(
                        "You cannot have duplicate resource names.") from sql3ie
                app.logger.debug(
                    f"{type(sql3ie)=}: {sql3ie=}")
                raise

@resources.route("/view/<uuid:resource_id>")
@require_oauth("profile group resource")
def view_resource(resource_id: uuid.UUID) -> Response:
    """View a particular resource's details."""
    with require_oauth.acquire("profile group resource") as the_token:
        db_uri = app.config["AUTH_DB"]
        with db.connection(db_uri) as conn:
            return jsonify(dictify(resource_by_id(
                conn, the_token.user, resource_id)))

def __safe_get_requests_page__(key: str = "page") -> int:
    """Get the results page if it exists or default to the first page."""
    try:
        return abs(int(request.args.get(key, "1"), base=10))
    except ValueError as _valerr:
        return 1

def __safe_get_requests_count__(key: str = "count_per_page") -> int:
    """Get the results page if it exists or default to the first page."""
    try:
        count = request.args.get(key, "0")
        if count != 0:
            return abs(int(count, base=10))
        return 0
    except ValueError as _valerr:
        return 0

@resources.route("/view/<uuid:resource_id>/data")
@require_oauth("profile group resource")
def view_resource_data(resource_id: uuid.UUID) -> Response:
    """Retrieve a particular resource's data."""
    with require_oauth.acquire("profile group resource") as the_token:
        db_uri = app.config["AUTH_DB"]
        count_per_page = __safe_get_requests_count__("count_per_page")
        offset = (__safe_get_requests_page__("page") - 1)
        with db.connection(db_uri) as conn:
            resource = resource_by_id(conn, the_token.user, resource_id)
            return jsonify(resource_data(
                conn,
                resource,
                ((offset * count_per_page) if bool(count_per_page) else offset),
                count_per_page))

@resources.route("/data/link", methods=["POST"])
@require_oauth("profile group resource")
def link_data():
    """Link group data to a specific resource."""
    try:
        form = request.form
        assert "resource_id" in form, "Resource ID not provided."
        assert "data_link_id" in form, "Data Link ID not provided."
        assert "dataset_type" in form, "Dataset type not specified"
        assert form["dataset_type"].lower() in (
            "mrna", "genotype", "phenotype"), "Invalid dataset type provided."

        with require_oauth.acquire("profile group resource") as the_token:
            def __link__(conn: db.DbConnection):
                return link_data_to_resource(
                    conn, the_token.user, uuid.UUID(form["resource_id"]),
                    form["dataset_type"], uuid.UUID(form["data_link_id"]))

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
        assert "data_link_id" in form, "Data Link ID not provided."

        with require_oauth.acquire("profile group resource") as the_token:
            def __unlink__(conn: db.DbConnection):
                return unlink_data_from_resource(
                    conn, the_token.user, uuid.UUID(form["resource_id"]),
                    uuid.UUID(form["data_link_id"]))
            return jsonify(with_db_connection(__unlink__))
    except AssertionError as aserr:
        raise InvalidData(aserr.args[0]) from aserr

@resources.route("<uuid:resource_id>/user/list", methods=["GET"])
@require_oauth("profile group resource")
def resource_users(resource_id: uuid.UUID):
    """Retrieve all users with access to the given resource."""
    with require_oauth.acquire("profile group resource") as the_token:
        def __the_users__(conn: db.DbConnection):
            resource = resource_by_id(conn, the_token.user, resource_id)
            authorised = authorised_for(
                conn, the_token.user, ("group:resource:edit-resource",),
                (resource_id,))
            if authorised.get(resource_id, False):
                with db.cursor(conn) as cursor:
                    def __organise_users_n_roles__(users_n_roles, row):
                        user_id = uuid.UUID(row["user_id"])
                        user = users_n_roles.get(user_id, {}).get(
                            "user", User(user_id, row["email"], row["name"]))
                        role = GroupRole(
                            uuid.UUID(row["group_role_id"]),
                            resource.group,
                            Role(uuid.UUID(row["role_id"]), row["role_name"],
                                 bool(int(row["user_editable"])), tuple()))
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

@resources.route("<uuid:resource_id>/user/assign", methods=["POST"])
@require_oauth("profile group resource role")
def assign_role_to_user(resource_id: uuid.UUID) -> Response:
    """Assign a role on the specified resource to a user."""
    with require_oauth.acquire("profile group resource role") as the_token:
        try:
            form = request.form
            group_role_id = form.get("group_role_id", "")
            user_email = form.get("user_email", "")
            assert bool(group_role_id), "The role must be provided."
            assert bool(user_email), "The user email must be provided."

            def __assign__(conn: db.DbConnection) -> dict:
                resource = resource_by_id(conn, the_token.user, resource_id)
                user = user_by_email(conn, user_email)
                return assign_resource_user(
                    conn, resource, user,
                    group_role_by_id(conn, resource.group,
                                     uuid.UUID(group_role_id)))
        except AssertionError as aserr:
            raise AuthorisationError(aserr.args[0]) from aserr

        return jsonify(with_db_connection(__assign__))

@resources.route("<uuid:resource_id>/user/unassign", methods=["POST"])
@require_oauth("profile group resource role")
def unassign_role_to_user(resource_id: uuid.UUID) -> Response:
    """Unassign a role on the specified resource from a user."""
    with require_oauth.acquire("profile group resource role") as the_token:
        try:
            form = request.form
            group_role_id = form.get("group_role_id", "")
            user_id = form.get("user_id", "")
            assert bool(group_role_id), "The role must be provided."
            assert bool(user_id), "The user id must be provided."

            def __assign__(conn: db.DbConnection) -> dict:
                resource = resource_by_id(conn, the_token.user, resource_id)
                return unassign_resource_user(
                    conn, resource, user_by_id(conn, uuid.UUID(user_id)),
                    group_role_by_id(conn, resource.group,
                                     uuid.UUID(group_role_id)))
        except AssertionError as aserr:
            raise AuthorisationError(aserr.args[0]) from aserr

        return jsonify(with_db_connection(__assign__))

@resources.route("<uuid:resource_id>/toggle-public", methods=["POST"])
@require_oauth("profile group resource role")
def toggle_public(resource_id: uuid.UUID) -> Response:
    """Make a resource public if it is private, or private if public."""
    with require_oauth.acquire("profile group resource") as the_token:
        def __toggle__(conn: db.DbConnection) -> Resource:
            old_rsc = resource_by_id(conn, the_token.user, resource_id)
            return save_resource(
                conn, the_token.user, Resource(
                    old_rsc.group, old_rsc.resource_id, old_rsc.resource_name,
                    old_rsc.resource_category, not old_rsc.public,
                    old_rsc.resource_data))

        resource = with_db_connection(__toggle__)
        return jsonify({
            "resource": dictify(resource),
            "description": (
                "Made resource public" if resource.public
                else "Made resource private")})
