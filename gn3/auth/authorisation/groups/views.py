"""The views/routes for the `gn3.auth.authorisation.groups` package."""
import uuid
import datetime
from typing import Iterable
from functools import partial

from MySQLdb.cursors import DictCursor
from flask import request, jsonify, Response, Blueprint, current_app

from gn3.auth import db
from gn3 import db_utils as gn3db

from gn3.auth.dictify import dictify
from gn3.auth.db_utils import with_db_connection

from .data import link_data_to_group
from .models import (
    Group, user_group, all_groups, DUMMY_GROUP, GroupRole, group_by_id,
    join_requests, group_role_by_id, GroupCreationError,
    accept_reject_join_request, group_users as _group_users,
    create_group as _create_group, add_privilege_to_group_role,
    delete_privilege_from_group_role, create_group_role as _create_group_role)

from ..roles.models import Role
from ..roles.models import user_roles

from ..checks import authorised_p
from ..privileges import Privilege, privileges_by_ids
from ..errors import InvalidData, NotFoundError, AuthorisationError

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
            group = user_group(conn, user).maybe(# type: ignore[misc]
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

def unlinked_mrna_data(
        conn: db.DbConnection, group: Group) -> tuple[dict, ...]:
    """
    Retrieve all mRNA Assay data linked to a group but not linked to any
    resource.
    """
    query = (
        "SELECT lmd.* FROM linked_mrna_data lmd "
        "LEFT JOIN mrna_resources mr ON lmd.data_link_id=mr.data_link_id "
        "WHERE lmd.group_id=? AND mr.data_link_id IS NULL")
    with db.cursor(conn) as cursor:
        cursor.execute(query, (str(group.group_id),))
        return tuple(dict(row) for row in cursor.fetchall())

def unlinked_genotype_data(
        conn: db.DbConnection, group: Group) -> tuple[dict, ...]:
    """
    Retrieve all genotype data linked to a group but not linked to any resource.
    """
    query = (
        "SELECT lgd.* FROM linked_genotype_data lgd "
        "LEFT JOIN genotype_resources gr ON lgd.data_link_id=gr.data_link_id "
        "WHERE lgd.group_id=? AND gr.data_link_id IS NULL")
    with db.cursor(conn) as cursor:
        cursor.execute(query, (str(group.group_id),))
        return tuple(dict(row) for row in cursor.fetchall())

def unlinked_phenotype_data(
        authconn: db.DbConnection, gn3conn: gn3db.Connection,
        group: Group) -> tuple[dict, ...]:
    """
    Retrieve all phenotype data linked to a group but not linked to any
    resource.
    """
    with db.cursor(authconn) as authcur, gn3conn.cursor(DictCursor) as gn3cur:
        authcur.execute(
            "SELECT lpd.* FROM linked_phenotype_data AS lpd "
            "LEFT JOIN phenotype_resources AS pr "
            "ON lpd.data_link_id=pr.data_link_id "
            "WHERE lpd.group_id=? AND pr.data_link_id IS NULL",
            (str(group.group_id),))
        results = authcur.fetchall()
        ids: dict[tuple[str, ...], str] = {
            (
                row["SpeciesId"], row["InbredSetId"], row["PublishFreezeId"],
                row["PublishXRefId"]): row["data_link_id"]
            for row in results
        }
        if len(ids.keys()) < 1:
            return tuple()
        paramstr = ", ".join(["(%s, %s, %s, %s)"] * len(ids.keys()))
        gn3cur.execute(
            "SELECT spc.SpeciesId, spc.SpeciesName, iset.InbredSetId, "
            "iset.InbredSetName, pf.Id AS PublishFreezeId, "
            "pf.Name AS dataset_name, pf.FullName AS dataset_fullname, "
            "pf.ShortName AS dataset_shortname, pxr.Id AS PublishXRefId, "
            "pub.PubMed_ID, pub.Title, pub.Year, "
            "phen.Pre_publication_description, "
            "phen.Post_publication_description, phen.Original_description "
            "FROM "
            "Species AS spc "
            "INNER JOIN InbredSet AS iset "
            "ON spc.SpeciesId=iset.SpeciesId "
            "INNER JOIN PublishFreeze AS pf "
            "ON iset.InbredSetId=pf.InbredSetId "
            "INNER JOIN PublishXRef AS pxr "
            "ON pf.InbredSetId=pxr.InbredSetId "
            "INNER JOIN Publication AS pub "
            "ON pxr.PublicationId=pub.Id "
            "INNER JOIN Phenotype AS phen "
            "ON pxr.PhenotypeId=phen.Id "
            "WHERE (spc.SpeciesId, iset.InbredSetId, pf.Id, pxr.Id) "
            f"IN ({paramstr})",
            tuple(item for sublist in ids.keys() for item in sublist))
        return tuple({
            **{key: value for key, value in row.items() if key not in
               ("Post_publication_description", "Pre_publication_description",
                "Original_description")},
            "description": (
                row["Post_publication_description"] or
                row["Pre_publication_description"] or
                row["Original_description"]),
            "data_link_id": ids[tuple(str(row[key]) for key in (
                "SpeciesId", "InbredSetId", "PublishFreezeId",
                "PublishXRefId"))]
        } for row in gn3cur.fetchall())

@groups.route("/<string:resource_type>/unlinked-data")
@require_oauth("profile group resource")
def unlinked_data(resource_type: str) -> Response:
    """View data linked to the group but not linked to any resource."""
    if resource_type not in ("all", "mrna", "genotype", "phenotype"):
        raise AuthorisationError(f"Invalid resource type {resource_type}")

    with require_oauth.acquire("profile group resource") as the_token:
        db_uri = current_app.config["AUTH_DB"]
        gn3db_uri = current_app.config["SQL_URI"]
        with (db.connection(db_uri) as authconn,
              gn3db.database_connection(gn3db_uri) as gn3conn):
            ugroup = user_group(authconn, the_token.user).maybe(# type: ignore[misc]
                DUMMY_GROUP, lambda grp: grp)
            if ugroup == DUMMY_GROUP:
                return jsonify(tuple())

            unlinked_fns = {
                "mrna": unlinked_mrna_data,
                "genotype": unlinked_genotype_data,
                "phenotype": lambda conn, grp: partial(
                    unlinked_phenotype_data, gn3conn=gn3conn)(
                        authconn=conn, group=grp)
            }
            return jsonify(tuple(
                dict(row) for row in unlinked_fns[resource_type](
                    authconn, ugroup)))

    return jsonify(tuple())

@groups.route("/data/link", methods=["POST"])
@require_oauth("profile group resource")
def link_data() -> Response:
    """Link selected data to specified group."""
    with require_oauth.acquire("profile group resource") as _the_token:
        form = request.form
        group_id = uuid.UUID(form["group_id"])
        dataset_ids = form.getlist("dataset_ids")
        dataset_type = form.get("dataset_type")
        if dataset_type not in ("mrna", "genotype", "phenotype"):
            raise InvalidData("Unexpected dataset type requested!")
        def __link__(conn: db.DbConnection):
            group = group_by_id(conn, group_id)
            with gn3db.database_connection(current_app.config["SQL_URI"]) as gn3conn:
                return link_data_to_group(
                    conn, gn3conn, dataset_type, dataset_ids, group)

        return jsonify(with_db_connection(__link__))

@groups.route("/roles", methods=["GET"])
@require_oauth("profile group")
def group_roles():
    """Return a list of all available group roles."""
    with require_oauth.acquire("profile group role") as the_token:
        def __list_roles__(conn: db.DbConnection):
            ## TODO: Check that user has appropriate privileges
            with db.cursor(conn) as cursor:
                group = user_group(conn, the_token.user).maybe(# type: ignore[misc]
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
                                   bool(int(row["user_editable"])),
                                   tuple()))
                    for row in cursor.fetchall())
        return jsonify(tuple(
            dictify(role) for role in with_db_connection(__list_roles__)))

@groups.route("/privileges", methods=["GET"])
@require_oauth("profile group")
def group_privileges():
    """Return a list of all available group roles."""
    with require_oauth.acquire("profile group role") as the_token:
        def __list_privileges__(conn: db.DbConnection) -> Iterable[Privilege]:
            ## TODO: Check that user has appropriate privileges
            this_user_roles = user_roles(conn, the_token.user)
            with db.cursor(conn) as cursor:
                cursor.execute("SELECT * FROM privileges "
                               "WHERE privilege_id LIKE 'group:%'")
                group_level_roles = tuple(
                    Privilege(row["privilege_id"], row["privilege_description"])
                    for row in cursor.fetchall())
            return tuple(privilege for arole in this_user_roles
                         for privilege in arole.privileges) + group_level_roles
        return jsonify(tuple(
            dictify(priv) for priv in with_db_connection(__list_privileges__)))



@groups.route("/role/create", methods=["POST"])
@require_oauth("profile group")
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

            group = user_group(conn, the_token.user).maybe(# type: ignore[misc]
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
@require_oauth("profile group")
def view_group_role(group_role_id: uuid.UUID):
    """Return the details of the given role."""
    with require_oauth.acquire("profile group role") as the_token:
        def __group_role__(conn: db.DbConnection) -> GroupRole:
            group = user_group(conn, the_token.user).maybe(#type: ignore[misc]
                DUMMY_GROUP, lambda grp: grp)

            if group == DUMMY_GROUP:
                raise AuthorisationError(
                    "A user without a group cannot view group roles.")
            return group_role_by_id(conn, group, group_role_id)
        return jsonify(dictify(with_db_connection(__group_role__)))

def __add_remove_priv_to_from_role__(conn: db.DbConnection,
                                     group_role_id: uuid.UUID,
                                     direction: str,
                                     user: User) -> GroupRole:
    assert direction in ("ADD", "DELETE")
    group = user_group(conn, user).maybe(# type: ignore[misc]
        DUMMY_GROUP, lambda grp: grp)

    if group == DUMMY_GROUP:
        raise AuthorisationError(
            "You need to be a member of a group to edit roles.")
    try:
        privilege_id = request.form.get("privilege_id", "")
        assert bool(privilege_id), "Privilege to add must be provided."
        privileges = privileges_by_ids(conn, (privilege_id,))
        if len(privileges) == 0:
            raise NotFoundError("Privilege not found.")
        dir_fns = {
            "ADD": add_privilege_to_group_role,
            "DELETE": delete_privilege_from_group_role
        }
        return dir_fns[direction](
            conn,
            group_role_by_id(conn, group, group_role_id),
            privileges[0])
    except AssertionError as aerr:
        raise InvalidData(aerr.args[0]) from aerr

@groups.route("/role/<uuid:group_role_id>/privilege/add", methods=["POST"])
@require_oauth("profile group")
def add_priv_to_role(group_role_id: uuid.UUID) -> Response:
    """Add privilege to group role."""
    with require_oauth.acquire("profile group role") as the_token:
        return jsonify({
            **dictify(with_db_connection(partial(
                __add_remove_priv_to_from_role__, group_role_id=group_role_id,
                direction="ADD", user=the_token.user))),
            "description": "Privilege added successfully"
        })

@groups.route("/role/<uuid:group_role_id>/privilege/delete", methods=["POST"])
@require_oauth("profile group")
def delete_priv_from_role(group_role_id: uuid.UUID) -> Response:
    """Delete privilege from group role."""
    with require_oauth.acquire("profile group role") as the_token:
        return jsonify({
            **dictify(with_db_connection(partial(
                __add_remove_priv_to_from_role__, group_role_id=group_role_id,
                direction="DELETE", user=the_token.user))),
            "description": "Privilege deleted successfully"
        })
