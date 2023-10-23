"""Implement case-attribute manipulations."""
import os
import csv
import json
import uuid
import requests
import tempfile
from enum import Enum, auto
from pathlib import Path
from functools import reduce
from datetime import datetime
from urllib.parse import urljoin

from MySQLdb.cursors import DictCursor
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

from gn3.auth.authorisation.users import User
from gn3.auth.authorisation.errors import AuthorisationError
from gn3.auth.authorisation.oauth2.resource_server import require_oauth

caseattr = Blueprint("case-attribute", __name__)

CATTR_DIFFS_DIR = "case-attribute-diffs"

class NoDiffError(ValueError):
    """Raised if there is no difference between the old and new data."""
    def __init__(self):
        """Initialise exception."""
        super().__init__(
            self, "No difference between existing data and sent data.")

class EditStatus(Enum):
    """Enumeration for the status of the edits."""
    review = auto()
    approved = auto()
    rejected = auto()

    def __str__(self):
        """Print out human-readable form."""
        return self.name

class CAJSONEncoder(json.JSONEncoder):
    """Encoder for CaseAttribute-specific data"""
    def default(self, obj):
        """Default encoder"""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

def required_access(inbredset_id: int, access_levels: tuple[str, ...]) -> bool:
    """Check whether the user has the appropriate access"""
    def __species_id__(conn):
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT SpeciesId FROM InbredSet WHERE InbredSetId=%s",
                (inbredset_id,))
            return cursor.fetchone()[0]
    try:
        with (require_oauth.acquire("profile resource") as the_token,
              database_connection(current_app.config["SQL_URI"]) as conn):
            result = requests.get(
                urljoin(current_app.config["AUTH_SERVER_URL"],
                        "auth/resource/inbredset/resource-id"
                        f"/{__species_id__(conn)}/{inbredset_id}"))
            if result.status_code == 200:
                resource_id = result.json()["resource-id"]
                auth = requests.post(
                    urljoin(current_app.config["AUTH_SERVER_URL"],
                            "auth/resource/authorisation"),
                    json={"resource-ids": [resource_id]},
                    headers={"Authorization": f"Bearer {the_token.access_token}"})
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
        strain_name: {
            **{
                key: value for key,value in item.items()
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
            "WHERE ca.InbredSetId=%(inbredset_id)s "
            "ORDER BY StrainName",
            {"inbredset_id": inbredset_id})
        return tuple(
            reduce(__by_strain__, cursor.fetchall(), {}).values())

@caseattr.route("/<int:inbredset_id>/values", methods=["GET"])
def inbredset_case_attribute_values(inbredset_id: int) -> Response:
    """Retrieve the group's (InbredSet's) case-attribute values."""
    with database_connection(current_app.config["SQL_URI"]) as conn:
        return jsonify(__case_attribute_values_by_inbred_set__(conn, inbredset_id))

def __process_orig_data__(fieldnames, cadata, strains) -> tuple[dict, ...]:
    """Process data from database and return tuple of dicts."""
    data = {item["StrainName"]: item for item in cadata}
    return tuple(
        {
            "Strain": strain["Name"],
            **{
                key: data.get(
                    strain["Name"], {}).get("case-attributes", {}).get(key, "")
                for key in fieldnames[1:]
            }
        } for strain in strains)

def __process_edit_data__(fieldnames, form_data) -> tuple[dict, ...]:
    """Process data from form and return tuple of dicts."""
    def __process__(acc, strain_cattrs):
        strain, cattrs = strain_cattrs
        return acc + ({
            "Strain": strain, **{
            field: cattrs["case-attributes"].get(field, "")
            for field in fieldnames[1:]
            }
        },)
    return reduce(__process__, form_data.items(), tuple())

def __write_csv__(fieldnames, data):
    """Write the given `data` to a csv file and return the path to the file."""
    fdesc, filepath = tempfile.mkstemp(".csv")
    os.close(fdesc)
    with open(filepath, "w", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect="unix")
        writer.writeheader()
        writer.writerows(data)

    return filepath

def __compute_diff__(
        fieldnames: tuple[str, ...],
        original_data: tuple[dict, ...],
        edit_data: tuple[dict, ...]):
    """Return the diff of the data."""
    basefilename = __write_csv__(fieldnames, original_data)
    deltafilename = __write_csv__(fieldnames, edit_data)
    diff_results = run_cmd(json.dumps(
        ["csvdiff", basefilename, deltafilename, "--format", "json"]))
    os.unlink(basefilename)
    os.unlink(deltafilename)
    if diff_results["code"] == 0:
        return json.loads(diff_results["output"])
    return {}

def __queue_diff__(conn: Connection, diff_data, diff_data_dir: Path) -> Path:
    """
    Queue diff for future processing.

    Returns: `diff`
        On success, this will return the filename where the diff was saved.
        On failure, it will raise a MySQL error.
    """
    diff = diff_data["diff"]
    if bool(diff["Additions"]) or bool(diff["Modifications"]) or bool(diff["Deletions"]):
        diff_data_dir.mkdir(parents=True, exist_ok=True)

        created = datetime.now()
        filepath = Path(
            diff_data_dir,
            f"{diff_data['inbredset_id']}:::{diff_data['user_id']}:::"
            f"{created.isoformat()}.json")
        with open(filepath, "w", encoding="utf8") as diff_file:
            # We want this to fail if the metadata items below are not provided.
            the_diff = {**diff_data, "created": created}
            insert_id = __save_diff__(conn, the_diff, EditStatus.review)
            diff_file.write(json.dumps({**the_diff, "db_id": insert_id},
                                       cls=CAJSONEncoder))
        return filepath
    raise NoDiffError

def __save_diff__(conn: Connection, diff_data: dict, status: EditStatus) -> int:
    """Save to the database."""
    with conn.cursor() as cursor:
        cursor.execute(
            "INSERT INTO "
            "caseattributes_audit(id, status, editor, json_diff_data, time_stamp) "
            "VALUES(%(db_id)s, %(status)s, %(editor)s, %(diff)s, %(ts)s) "
            "ON DUPLICATE KEY UPDATE status=%(status)s",
            {
                "db_id": diff_data.get("db_id"),
                "status": str(status),
                "editor": str(diff_data["user_id"]),
                "diff": json.dumps(diff_data, cls=CAJSONEncoder),
                "ts": diff_data["created"].isoformat()
            })
        return diff_data.get("db_id") or cursor.lastrowid

def __parse_diff_json__(json_str):
    """Parse the json string to python objects."""
    raw_diff = json.loads(json_str)
    return {
        **raw_diff,
        "db_id": int(raw_diff["db_id"]) if raw_diff.get("db_id") else None,
        "inbredset_id": (int(raw_diff["inbredset_id"])
                         if raw_diff.get("inbredset_id") else None),
        "user_id": (uuid.UUID(raw_diff["user_id"])
                    if raw_diff.get("user_id") else None),
        "created": (datetime.fromisoformat(raw_diff["created"])
                    if raw_diff.get("created") else None)
    }

def __load_diff__(diff_filename):
    """Load the diff."""
    with open(diff_filename, encoding="utf8") as diff_file:
        return __parse_diff_json__(diff_file.read())

def __apply_diff__(
        conn: Connection, inbredset_id: int, user: User, diff_filename) -> None:
    """
    Apply the changes in the diff at `diff_filename` to the data in the database
    if the user has appropriate privileges.
    """
    required_access(
        inbredset_id, ("system:inbredset:edit-case-attribute",
                       "system:inbredset:apply-case-attribute-edit"))
    raise NotImplementedError

def __reject_diff__(conn: Connection,
                    inbredset_id: int,
                    user: User,
                    diff_filename: Path,
                    diff: dict) -> Path:
    """
    Reject the changes in the diff at `diff_filename` to the data in the
    database if the user has appropriate privileges.
    """
    required_access(
        inbredset_id, ("system:inbredset:edit-case-attribute",
                       "system:inbredset:apply-case-attribute-edit"))
    __save_diff__(conn, diff, EditStatus.rejected)
    new_path = Path(diff_filename.parent, f"{diff_filename.stem}-rejected{diff_filename.suffix}")
    os.rename(diff_filename, new_path)
    return diff_filename

@caseattr.route("/<int:inbredset_id>/add", methods=["POST"])
def add_case_attributes(inbredset_id: int) -> Response:
    """Add a new case attribute for `InbredSetId`."""
    required_access(inbredset_id, ("system:inbredset:create-case-attribute",))
    with (require_oauth.acquire("profile resource") as the_token,
          database_connection(current_app.config["SQL_URI"]) as conn):
        raise NotImplementedError

@caseattr.route("/<int:inbredset_id>/delete", methods=["POST"])
def delete_case_attributes(inbredset_id: int) -> Response:
    """Delete a case attribute from `InbredSetId`."""
    required_access(inbredset_id, ("system:inbredset:delete-case-attribute",))
    with (require_oauth.acquire("profile resource") as the_token,
          database_connection(current_app.config["SQL_URI"]) as conn):
        raise NotImplementedError

@caseattr.route("/<int:inbredset_id>/edit", methods=["POST"])
def edit_case_attributes(inbredset_id: int) -> Response:
    """Edit the case attributes for `InbredSetId` based on data received."""
    with (require_oauth.acquire("profile resource") as the_token,
          database_connection(current_app.config["SQL_URI"]) as conn):
        required_access(inbredset_id,
                        ("system:inbredset:edit-case-attribute",))
        user = the_token.user
        fieldnames = (["Strain"] + sorted(
            attr["Name"] for attr in
            __case_attribute_labels_by_inbred_set__(conn, inbredset_id)))
        try:
            diff_filename = __queue_diff__(
                conn, {
                    "inbredset_id": inbredset_id,
                    "user_id": str(user.user_id),
                    "fieldnames": fieldnames,
                    "diff": __compute_diff__(
                        fieldnames,
                        __process_orig_data__(
                            fieldnames,
                            __case_attribute_values_by_inbred_set__(conn, inbredset_id),
                            __inbredset_strains__(conn, inbredset_id)),
                        __process_edit_data__(fieldnames, request.json["edit-data"]))
                },
                Path(current_app.config.get("TMPDIR"), CATTR_DIFFS_DIR))
        except NoDiffError as _nde:
            msg = "There were no changes to make from submitted data."
            response = jsonify({
                "diff-status": "error",
                "error_description": msg
            })
            response.status_code = 400
            return response

        try:
            __apply_diff__(conn, user, diff_filename)
            return jsonify({
                "diff-status": "applied",
                "message": ("The changes to the case-attributes have been "
                            "applied successfully.")
            })
        except AuthorisationError as _auth_err:
            return jsonify({
                "diff-status": "queued",
                "message": ("The changes to the case-attributes have been "
                            "queued for approval."),
                "diff-filename": str(diff_filename.name)
            })

@caseattr.route("/<int:inbredset_id>/diff/list", methods=["GET"])
def list_diffs(inbredset_id: int) -> Response:
    """List any changes that have not been approved/rejected."""
    Path(current_app.config.get("TMPDIR"), CATTR_DIFFS_DIR).mkdir(
        parents=True, exist_ok=True)

    def __generate_diff_files__(diffs):
        diff_dir = Path(current_app.config.get("TMPDIR"), CATTR_DIFFS_DIR)
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
def approve_case_attributes_diff(inbredset_id: int) -> Response:
    """Approve the changes to the case attributes in the diff."""
    with (require_oauth.acquire("profile resource") as the_token,
          database_connection(current_app.config["SQL_URI"]) as conn):
        __apply_diff__(conn, inbredset_id, the_token.user, diff_filename)
        raise NotImplementedError

@caseattr.route("/reject/<path:filename>", methods=["POST"])
def reject_case_attributes_diff(filename: str) -> Response:
    """Reject the changes to the case attributes in the diff."""
    diff_dir = Path(current_app.config.get("TMPDIR"), CATTR_DIFFS_DIR)
    diff_filename = Path(diff_dir, filename)
    the_diff = __load_diff__(diff_filename)
    with (require_oauth.acquire("profile resource") as the_token,
          database_connection(current_app.config["SQL_URI"]) as conn):
        __reject_diff__(conn, the_diff["inbredset_id"], the_token.user, diff_filename, the_diff)
        return jsonify({
            "message": f"Rejected diff successfully",
            "diff_filename": diff_filename.name
        })

@caseattr.route("/<int:inbredset_id>/diff/<int:diff_id>/view", methods=["GET"])
def view_diff(inbredset_id: int, diff_id: int) -> Response:
    """View a diff."""
    with (require_oauth.acquire("profile resource") as the_token,
          database_connection(current_app.config["SQL_URI"]) as conn,
          conn.cursor(cursorclass=DictCursor) as cursor):
        required_access(inbredset_id, ("system:inbredset:view-case-attribute",))
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
                    "created": diff["time_stamp"],
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
