"""The views/routes for the `gn3.auth.authorisation.groups` package."""
import uuid
import datetime
from typing import Iterable
from functools import partial

from flask import request, jsonify, Response, Blueprint, current_app

from gn3.auth import db
from gn3 import db_utils as gn3dbutils

from gn3.auth.dictify import dictify
from gn3.auth.db_utils import with_db_connection

from .data import link_data_to_group, retrieve_ungrouped_data
from .models import (
    user_group, all_groups, DUMMY_GROUP, GroupRole, group_by_id, join_requests,
    group_role_by_id, GroupCreationError, accept_reject_join_request,
    group_users as _group_users, create_group as _create_group,
    create_group_role as _create_group_role)

from ..roles.models import Role
from ..checks import authorised_p
from ..privileges import Privilege, privileges_by_ids
from ..errors import InvalidData, AuthorisationError

from ...authentication.users import User
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

@groups.route("/requests/join/<uuid:group_id>", methods=["POST"])
@require_oauth("profile group")
def request_to_join(group_id: uuid.UUID) -> Response:
    """Request to join a group."""
    def __request__(conn: db.DbConnection, user: User, group_id: uuid.UUID,
                    message: str):
        with db.cursor(conn) as cursor:
            group = user_group(cursor, user).maybe(# type: ignore[misc]
                False, lambda grp: grp)# type: ignore[arg-type]
            if group:
                error = AuthorisationError(
                    "You cannot request to join a new group while being a "
                    "member of an existing group.")
                error.error_code = 400
                raise error
            request_id = uuid.uuid4()
            cursor.execute(
                "INSERT INTO group_join_requests VALUES "
                "(:request_id, :group_id, :user_id, :ts, :status, :msg)",
                {
                    "request_id": str(request_id),
                    "group_id": str(group_id),
                    "user_id": str(user.user_id),
                    "ts": datetime.datetime.now().timestamp(),
                    "status": "PENDING",
                    "msg": message
                })
            return {
                "request_id":  request_id,
                "message": "Successfully sent the join request."
            }

    with require_oauth.acquire("profile group") as the_token:
        form = request.form
        results = with_db_connection(partial(
            __request__, user=the_token.user, group_id=group_id, message=form.get(
                "message", "I hereby request that you add me to your group.")))
        return jsonify(results)

@groups.route("/requests/join/list", methods=["GET"])
@require_oauth("profile group")
def list_join_requests() -> Response:
    """List the pending join requests."""
    with require_oauth.acquire("profile group") as the_token:
        return jsonify(with_db_connection(partial(
            join_requests, user=the_token.user)))

@groups.route("/requests/join/accept", methods=["POST"])
@require_oauth("profile group")
def accept_join_requests() -> Response:
    """Accept a join request."""
    with require_oauth.acquire("profile group") as the_token:
        form = request.form
        request_id = uuid.UUID(form.get("request_id"))
        return jsonify(with_db_connection(partial(
            accept_reject_join_request, request_id=request_id,
            user=the_token.user, status="ACCEPTED")))

@groups.route("/requests/join/reject", methods=["POST"])
@require_oauth("profile group")
def reject_join_requests() -> Response:
    """Reject a join request."""
    with require_oauth.acquire("profile group") as the_token:
        form = request.form
        request_id = uuid.UUID(form.get("request_id"))
        return jsonify(with_db_connection(partial(
            accept_reject_join_request, request_id=request_id,
            user=the_token.user, status="REJECTED")))

@groups.route("/<string:resource_type>/unlinked-data")
@require_oauth("profile group resource")
def unlinked_data(resource_type: str) -> Response:
    """View data linked to the group but not linked to any resource."""
    if resource_type not in ("all", "mrna", "genotype", "phenotype"):
        raise AuthorisationError(f"Invalid resource type {resource_type}")

    with require_oauth.acquire("profile group resource") as the_token:
        db_uri = current_app.config["AUTH_DB"]
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

            ids_query = (
                "SELECT * FROM ("
                "SELECT group_id, dataset_type, dataset_or_trait_id "
                "FROM linked_group_data "
                f"EXCEPT SELECT * FROM ({except_filter})"
                f") {type_filter}")
            cursor.execute(ids_query)
            ids = cursor.fetchall()
            print(f"THE IDS: {ids} ==> {type_filter}")

            if ids:
                clause = ", ".join(["(?, ?, ?)"] * len(ids))
                data_query = (
                    "SELECT * FROM linked_group_data "
                    "WHERE (group_id, dataset_type, dataset_or_trait_id) "
                    f"IN (VALUES {clause}) ")
                params = tuple(item for sublist in
                               ((row[0], row[1], row[2]) for row in ids)
                               for item in sublist)
                cursor.execute(data_query, params)
                return jsonify(tuple(dict(row) for row in cursor.fetchall()))

    return jsonify(tuple())

@groups.route("/<string:dataset_type>/ungrouped-data", methods=["GET"])
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

@groups.route("/data/link", methods=["POST"])
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

@groups.route("/roles", methods=["GET"])
def group_roles():
    """Return a list of all available group roles."""
    with require_oauth.acquire("profile group role") as the_token:
        def __list_roles__(conn: db.DbConnection):
            ## TODO: Check that user has appropriate privileges
            with db.cursor(conn) as cursor:
                group = user_group(cursor, the_token.user).maybe(# type: ignore[misc]
                    DUMMY_GROUP, lambda grp: grp)
                if group == DUMMY_GROUP:
                    return tuple()
                cursor.execute(
                    "SELECT gr.group_role_id, r.* "
                    "FROM group_roles AS gr INNER JOIN roles AS r "
                    "ON gr.role_id=r.role_id "
                    "WHERE group_id=?",
                    (str(group.group_id),))
                return tuple(
                    GroupRole(uuid.UUID(row["group_role_id"]),
                              group,
                              Role(uuid.UUID(row["role_id"]),
                                   row["role_name"],
                                   tuple()))
                    for row in cursor.fetchall())
        return jsonify(tuple(
            dictify(role) for role in with_db_connection(__list_roles__)))

@groups.route("/privileges", methods=["GET"])
def group_privileges():
    """Return a list of all available group roles."""
    with require_oauth.acquire("profile group role") as _the_token:
        def __list_privileges__(conn: db.DbConnection) -> Iterable[Privilege]:
            ## TODO: Check that user has appropriate privileges
            with db.cursor(conn) as cursor:
                cursor.execute("SELECT * FROM privileges "
                               "WHERE privilege_id LIKE 'group:%'")
                return (
                    Privilege(row["privilege_id"], row["privilege_description"])
                    for row in cursor.fetchall())
        return jsonify(tuple(
            dictify(priv) for priv in with_db_connection(__list_privileges__)))



@groups.route("/role/create", methods=["POST"])
def create_group_role():
    """Create a new group role."""
    with require_oauth.acquire("profile group role") as the_token:
        ## TODO: Check that user has appropriate privileges
        @authorised_p(("group:role:create-role",),
                      "You do not have the privilege to create new roles",
                      oauth2_scope="profile group role")
        def __create__(conn: db.DbConnection) -> GroupRole:
            ## TODO: Check user cannot assign any privilege they don't have.
            form = request.form
            role_name = form.get("role_name", "").strip()
            privileges_ids = form.getlist("privileges[]")
            if len(role_name) == 0:
                raise InvalidData("Role name not provided!")
            if len(privileges_ids) == 0:
                raise InvalidData(
                    "At least one privilege needs to be provided.")

            with db.cursor(conn) as cursor:
                group = user_group(cursor, the_token.user).maybe(# type: ignore[misc]
                    DUMMY_GROUP, lambda grp: grp)

            if group == DUMMY_GROUP:
                raise AuthorisationError(
                    "A user without a group cannot create a new role.")
            privileges = privileges_by_ids(conn, tuple(privileges_ids))
            if len(privileges_ids) != len(privileges):
                raise InvalidData(
                    f"{len(privileges_ids) - len(privileges)} of the selected "
                    "privileges were not found in the database.")

            return _create_group_role(conn, group, role_name, privileges)

        return jsonify(with_db_connection(__create__))

@groups.route("/role/<uuid:group_role_id>", methods=["GET"])
def view_group_role(group_role_id: uuid.UUID):
    """Return the details of the given role."""
    with require_oauth.acquire("profile group role") as the_token:
        def __group_role__(conn: db.DbConnection) -> GroupRole:
            with db.cursor(conn) as cursor:
                group = user_group(cursor, the_token.user).maybe(#type: ignore[misc]
                    DUMMY_GROUP, lambda grp: grp)

            if group == DUMMY_GROUP:
                raise AuthorisationError(
                    "A user without a group cannot view group roles.")
            return group_role_by_id(conn, group, group_role_id)
        return jsonify(dictify(with_db_connection(__group_role__)))
