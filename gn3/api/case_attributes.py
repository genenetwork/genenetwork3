"""Implement case-attribute manipulations."""
import os
import csv
import json
import uuid
import tempfile
import lmdb
from typing import Union

from pathlib import Path
from functools import reduce
from datetime import datetime
from urllib.parse import urljoin

import requests
from MySQLdb.cursors import DictCursor
from gn3.db.case_attributes import (
    CaseAttributeEdit,
    EditStatus,
    view_change,
from authlib.integrations.flask_oauth2.errors import _HTTPException
from flask import (
    jsonify,
    request,
    Response,
    Blueprint,
    current_app,
    make_response)

from gn3.commands import run_cmd

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
        required_access(auth_token,
                        inbredset_id,
                        ("system:inbredset:edit-case-attribute",))
        data = request.json["edit-data"]
        modified = {
            "inbredset_id": inbredset_id,
            "Modifications": {},
        }
        modifications, current = {}, {}

        for key, value in data.items():
            strain, case_attribute = key.split(":")
            if not current.get(strain):
                current[strain] = {}
            current[strain][case_attribute] = data.get(key)["Original"]
            if not modifications.get(strain):
                modifications[strain] = {}
            modifications[strain][case_attribute] = data.get(key)["Current"]
        modified["Modifications"]["Original"] = modifications
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
            edit.status = EditStatus.approved
            match update_case_attributes(cursor=cursor, change_id=_id, edit=edit):
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
            })


@caseattr.route("/<int:inbredset_id>/diff/list", methods=["GET"])
def list_diffs(inbredset_id: int) -> Response:
    """List any changes that have not been approved/rejected."""
    Path(current_app.config["TMPDIR"], CATTR_DIFFS_DIR).mkdir(
        parents=True, exist_ok=True)

    def __generate_diff_files__(diffs):
        diff_dir = Path(current_app.config["TMPDIR"], CATTR_DIFFS_DIR)
        review_files = set(afile.name for afile in diff_dir.iterdir()
                           if ("-rejected" not in afile.name
                               and "-approved" not in afile.name))
        for diff in diffs:
            the_diff = diff["json_diff_data"]
            diff_filepath = Path(
                diff_dir,
                f"{the_diff['inbredset_id']}:::{the_diff['user_id']}:::"
                f"{the_diff['created'].isoformat()}.json")
            if diff_filepath not in review_files:
                with open(diff_filepath, "w", encoding="utf-8") as dfile:
                    dfile.write(json.dumps(
                        {**the_diff, "db_id": diff["id"]},
                        cls=CAJSONEncoder))

    with (database_connection(current_app.config["SQL_URI"]) as conn,
          conn.cursor(cursorclass=DictCursor) as cursor):
        cursor.execute(
            "SELECT * FROM caseattributes_audit WHERE status='review'")
        diffs = tuple({
            **row,
            "json_diff_data": {
                **__parse_diff_json__(row["json_diff_data"]),
                "db_id": row["id"],
                "created": row["time_stamp"],
                "user_id": uuid.UUID(row["editor"])
            }
        } for row in cursor.fetchall())

    __generate_diff_files__(diffs)
    resp = make_response(json.dumps(
        tuple({
            **diff,
            "filename": (
                f"{diff['json_diff_data']['inbredset_id']}:::"
                f"{diff['json_diff_data']['user_id']}:::"
                f"{diff['time_stamp'].isoformat()}")
        } for diff in diffs
            if diff["json_diff_data"].get("inbredset_id") == inbredset_id),
        cls=CAJSONEncoder))
    resp.headers["Content-Type"] = "application/json"
    return resp


@caseattr.route("/approve/<path:filename>", methods=["POST"])
@require_token
def approve_case_attributes_diff(filename: str, auth_token=None) -> Response:
    """Approve the changes to the case attributes in the diff."""
    diff_dir = Path(current_app.config["TMPDIR"], CATTR_DIFFS_DIR)
    diff_filename = Path(diff_dir, filename)
    the_diff = __load_diff__(diff_filename)
    with database_connection(current_app.config["SQL_URI"]) as conn:
        __apply_diff__(conn, auth_token,
                       the_diff["inbredset_id"], diff_filename, the_diff)
        return jsonify({
            "message": "Applied the diff successfully.",
            "diff_filename": diff_filename.name
        })


@caseattr.route("/reject/<path:filename>", methods=["POST"])
@require_token
def reject_case_attributes_diff(filename: str, auth_token=None) -> Response:
    """Reject the changes to the case attributes in the diff."""
    diff_dir = Path(current_app.config["TMPDIR"], CATTR_DIFFS_DIR)
    diff_filename = Path(diff_dir, filename)
    the_diff = __load_diff__(diff_filename)
    with database_connection(current_app.config["SQL_URI"]) as conn:
        __reject_diff__(conn,
                        auth_token,
                        the_diff["inbredset_id"],
                        diff_filename,
                        the_diff)
        return jsonify({
            "message": "Rejected diff successfully",
            "diff_filename": diff_filename.name
        })


@caseattr.route("/<int:inbredset_id>/diff/<int:diff_id>/view", methods=["GET"])
@require_token
def view_diff(inbredset_id: int, diff_id: int, auth_token=None) -> Response:
    """View a diff."""
    with (database_connection(current_app.config["SQL_URI"]) as conn,
          conn.cursor(cursorclass=DictCursor) as cursor):
        required_access(
            auth_token, inbredset_id, ("system:inbredset:view-case-attribute",))
        cursor.execute(
            "SELECT * FROM caseattributes_audit WHERE id=%s",
            (diff_id,))
        diff = cursor.fetchone()
        if diff:
            json_diff_data = __parse_diff_json__(diff["json_diff_data"])
            if json_diff_data["inbredset_id"] != inbredset_id:
                return jsonify({
                    "error": "Not Found",
                    "error_description": (
                        "Could not find diff with the given ID for the "
                        "InbredSet chosen.")
                })
            return jsonify({
                **diff,
                "json_diff_data": {
                    **json_diff_data,
                    "db_id": diff["id"],
                    "created": diff["time_stamp"].isoformat(),
                    "user_id": uuid.UUID(diff["editor"])
                }
            })
        return jsonify({
            "error": "Not Found",
            "error_description": "Could not find diff with the given ID."
        })
    return jsonify({
        "error": "Code Error",
        "error_description": "The code should never run this."
    }), 500
