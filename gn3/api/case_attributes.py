"""Implement case-attribute manipulations."""
from typing import Union

from functools import reduce
from urllib.parse import urljoin

import requests
from MySQLdb.cursors import DictCursor
from gn3.db.case_attributes import (
    CaseAttributeEdit,
    EditStatus,
    view_change,
    queue_edit,
    apply_change,
    get_changes)
from authlib.integrations.flask_oauth2.errors import _HTTPException
from flask import (
    jsonify,
    request,
    Response,
    Blueprint,
    current_app)


from gn3.db_utils import Connection, database_connection

from gn3.oauth2.authorisation import require_token
from gn3.oauth2.errors import AuthorisationError

caseattr = Blueprint("case-attribute", __name__)


def required_access(
        token: dict,
        inbredset_id: int,
        access_levels: tuple[str, ...]
) -> Union[bool, tuple[str, ...]]:
    """Check whether the user has the appropriate access"""
    def __species_id__(conn):
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT SpeciesId FROM InbredSet WHERE InbredSetId=%s",
                (inbredset_id,))
            return cursor.fetchone()[0]
    try:
        with database_connection(current_app.config["SQL_URI"]) as conn:
            result = requests.get(
                # this section fetches the resource ID from the auth server
                urljoin(current_app.config["AUTH_SERVER_URL"],
                        "auth/resource/populations/resource-id"
                        f"/{__species_id__(conn)}/{inbredset_id}"),
                timeout=300)
            if result.status_code == 200:
                resource_id = result.json()["resource-id"]
                auth = requests.post(
                    # this section fetches the authorisations/privileges that
                    # the current user has on the resource we got above
                    urljoin(current_app.config["AUTH_SERVER_URL"],
                            "auth/resource/authorisation"),
                    json={"resource-ids": [resource_id]},
                    headers={
                        "Authorization": f"Bearer {token['access_token']}"},
                    timeout=300)
                if auth.status_code == 200:
                    privs = tuple(priv["privilege_id"]
                                  for role in auth.json()[resource_id]["roles"]
                                  for priv in role["privileges"])
                    if all(lvl in privs for lvl in access_levels):
                        return privs
    except _HTTPException as httpe:
        raise AuthorisationError("You need to be logged in.") from httpe

    raise AuthorisationError(
        f"User does not have the privileges {access_levels}")


def __inbredset_group__(conn, inbredset_id):
    """Return InbredSet group's top-level details."""
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            "SELECT * FROM InbredSet WHERE InbredSetId=%(inbredset_id)s",
            {"inbredset_id": inbredset_id})
        return dict(cursor.fetchone())


def __inbredset_strains__(conn, inbredset_id):
    """Return all samples/strains for given InbredSet group."""
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            "SELECT s.* FROM StrainXRef AS sxr INNER JOIN Strain AS s "
            "ON sxr.StrainId=s.Id WHERE sxr.InbredSetId=%(inbredset_id)s "
            "ORDER BY s.Name ASC",
            {"inbredset_id": inbredset_id})
        return tuple(dict(row) for row in cursor.fetchall())


def __case_attribute_labels_by_inbred_set__(conn, inbredset_id):
    """Return the case-attribute labels/names for the given InbredSet group."""
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            "SELECT * FROM CaseAttribute WHERE InbredSetId=%(inbredset_id)s",
            {"inbredset_id": inbredset_id})
        return tuple(dict(row) for row in cursor.fetchall())


@caseattr.route("/<int:inbredset_id>", methods=["GET"])
def inbredset_group(inbredset_id: int) -> Response:
    """Retrieve InbredSet group's details."""
    with database_connection(current_app.config["SQL_URI"]) as conn:
        return jsonify(__inbredset_group__(conn, inbredset_id))


@caseattr.route("/<int:inbredset_id>/strains", methods=["GET"])
def inbredset_strains(inbredset_id: int) -> Response:
    """Retrieve ALL strains/samples relating to a specific InbredSet group."""
    with database_connection(current_app.config["SQL_URI"]) as conn:
        return jsonify(__inbredset_strains__(conn, inbredset_id))


@caseattr.route("/<int:inbredset_id>/names", methods=["GET"])
def inbredset_case_attribute_names(inbredset_id: int) -> Response:
    """Retrieve ALL case-attributes for a specific InbredSet group."""
    with database_connection(current_app.config["SQL_URI"]) as conn:
        return jsonify(
            __case_attribute_labels_by_inbred_set__(conn, inbredset_id))


def __by_strain__(accumulator, item):
    attr = {item["CaseAttributeName"]: item["CaseAttributeValue"]}
    strain_name = item["StrainName"]
    if bool(accumulator.get(strain_name)):
        return {
            **accumulator,
            strain_name: {
                **accumulator[strain_name],
                "case-attributes": {
                    **accumulator[strain_name]["case-attributes"],
                    **attr
                }
            }
        }
    return {
        **accumulator,
        strain_name: {
            **{
                key: value for key, value in item.items()
                if key in ("StrainName", "StrainName2", "Symbol", "Alias")
            },
            "case-attributes": attr
        }
    }


def __case_attribute_values_by_inbred_set__(
        conn: Connection, inbredset_id: int) -> tuple[dict, ...]:
    """
    Retrieve Case-Attributes by their InbredSet ID. Do not call this outside
    this module.
    """
    with conn.cursor(cursorclass=DictCursor) as cursor:
        cursor.execute(
            "SELECT ca.Name AS CaseAttributeName, "
            "caxrn.Value AS CaseAttributeValue, s.Name AS StrainName, "
            "s.Name2 AS StrainName2, s.Symbol, s.Alias "
            "FROM CaseAttribute AS ca "
            "INNER JOIN CaseAttributeXRefNew AS caxrn "
            "ON ca.CaseAttributeId=caxrn.CaseAttributeId "
            "INNER JOIN Strain AS s "
            "ON caxrn.StrainId=s.Id "
            "WHERE caxrn.InbredSetId=%(inbredset_id)s "
            "ORDER BY StrainName",
            {"inbredset_id": inbredset_id})
        return tuple(
            reduce(__by_strain__, cursor.fetchall(), {}).values())


@caseattr.route("/<int:inbredset_id>/values", methods=["GET"])
def inbredset_case_attribute_values(inbredset_id: int) -> Response:
    """Retrieve the group's (InbredSet's) case-attribute values."""
    with database_connection(current_app.config["SQL_URI"]) as conn:
        return jsonify(__case_attribute_values_by_inbred_set__(conn, inbredset_id))


@caseattr.route("/<int:inbredset_id>/edit", methods=["POST"])
@require_token
def edit_case_attributes(inbredset_id: int, auth_token=None) -> Response:
    """Edit the case attributes for `InbredSetId` based on data received.

    :inbredset_id: Identifier for the population that the case attribute belongs
    :auth_token: A validated JWT from the auth server
    """
    with database_connection(current_app.config["SQL_URI"]) as conn, conn.cursor() as cursor:
        data = request.json["edit-data"]
        modified = {
            "inbredset_id": inbredset_id,
            "Modifications": {},
        }
        original, current = {}, {}

        for key, value in data.items():
            strain, case_attribute = key.split(":")
            if not current.get(strain):
                current[strain] = {}
            current[strain][case_attribute] = value["Current"]
            if not original.get(strain):
                original[strain] = {}
            original[strain][case_attribute] = value["Original"]
        modified["Modifications"]["Original"] = original
        modified["Modifications"]["Current"] = current
        edit = CaseAttributeEdit(
            inbredset_id=inbredset_id,
            status=EditStatus.review,
            user_id=auth_token["jwt"]["sub"],
            changes=modified
        )
        _id = queue_edit(cursor=cursor,
                         directory=current_app.config["LMDB_DATA_PATH"],
                         edit=edit)
        try:
            required_access(auth_token,
                            inbredset_id,
                            ("system:inbredset:edit-case-attribute",
                             "system:inbredset:apply-case-attribute-edit"))
            match apply_change(
                    cursor, change_type=EditStatus.approved,
                    change_id=_id,
                    directory=directory
            ):
                case True:
                    return jsonify({
                        "diff-status": "applied",
                        "message": ("The changes to the case-attributes have been "
                                    "applied successfully.")
                    })
                case _:
                    return jsonify({
                        "diff-status": "no changes to be applied",
                        "message": ("There were no changes to be made ")
                    })
        except AuthorisationError as _auth_err:
            return jsonify({
                "diff-status": "queued",
                "message": ("The changes to the case-attributes have been "
                            "queued for approval."),
            }), 401


@caseattr.route("/<int:inbredset_id>/diff/list", methods=["GET"])
def list_diffs(inbredset_id: int) -> Response:
    """List any changes that have not been approved/rejected."""
    try:
        required_access(auth_token,
                        inbredset_id,
                        ("system:inbredset:edit-case-attribute",
                         "system:inbredset:apply-case-attribute-edit"))
        with (database_connection(current_app.config["SQL_URI"]) as conn,
              conn.cursor(cursorclass=DictCursor) as cursor):
            changes = get_changes(cursor, inbredset_id=inbredset_id,
                                  directory=current_app.config["LMDB_DATA_PATH"])
            current_app.logger.error(changes)
            return jsonify(
                changes
            ), 200
    except AuthorisationError as _auth_err:
        return jsonify({
            "message": ("You are not authorised to list diffs."),
        }), 401


@caseattr.route("/approve/<int:change_id>", methods=["POST"])
@require_token
def approve_case_attributes_diff(filename: str, auth_token=None) -> Response:
    """Approve the changes to the case attributes in the diff."""
    try:
        required_access(auth_token,
                        inbredset_id,
                        ("system:inbredset:edit-case-attribute"))
        with database_connection(current_app.config["SQL_URI"]) as conn, \
                conn.cursor() as cursor:
            match apply_change(cursor, change_type=EditStatus.rejected,
                               directory=directory):
                case True:
                    return jsonify({
                        "diff-status": "rejected",
                        "message": (f"Successfully approved # {change_id}")
                    })
                case _:
                    return jsonify({
                        "diff-status": "queued",
                        "message": (f"Was not able to successfully approve # {change_id}")
                    })
    except AuthorisationError as __auth_err:
        return jsonify({
            "diff-status": "queued",
            "message": ("You don't have the right privileges to edit this resource.")
        }), 401


@caseattr.route("/reject/<int:change_id>", methods=["POST"])
@require_token
def reject_case_attributes_diff(filename: str, auth_token=None) -> Response:
    """Reject the changes to the case attributes in the diff."""
    try:
        required_access(auth_token,
                        inbredset_id,
                        ("system:inbredset:edit-case-attribute",
                         "system:inbredset:apply-case-attribute-edit"))
        with database_connection(current_app.config["SQL_URI"]) as conn, \
                conn.cursor() as cursor:
            match apply_change(cursor, change_type=EditStatus.rejected,
                               directory=directory):
                case True:
                    return jsonify({
                        "diff-status": "rejected",
                        "message": ("The changes to the case-attributes have been "
                                    "rejected.")
                    })
                case _:
                    return jsonify({
                        "diff-status": "queued",
                        "message": ("Failed to reject changes")
                    })
    except AuthorisationError as __auth_err:
        return jsonify({
            "message": ("You don't have the right privileges to edit this resource.")
        }), 401


@caseattr.route("/<int:change_id>/diff/view", methods=["GET"])
@require_token
def view_diff(inbredset_id: int, diff_id: int, auth_token=None) -> Response:
    """View a diff."""
    try:
        required_access(
            auth_token, inbredset_id, ("system:inbredset:view-case-attribute",))
        with (database_connection(current_app.config["SQL_URI"]) as conn,
              conn.cursor(cursorclass=DictCursor) as cursor):
            return jsonify(
                view_change(cursor, change_id)
            )
    except AuthorisationError as __auth_err:
        return jsonify({
            "message": ("You don't have the right privileges to view the diffs.")
        }), 401
