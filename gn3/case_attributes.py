"""Implement case-attribute manipulations."""
from functools import reduce

from MySQLdb.cursors import DictCursor
from flask import jsonify, Response, Blueprint, current_app

from gn3.db_utils import Connection, database_connection

from gn3.auth.authentication.users import User
from gn3.auth.authentication.oauth2.resource_server import require_oauth

from gn3.auth.authorisation.errors import AuthorisationError

caseattr = Blueprint("case-attribute", __name__)

@caseattr.route("/<int:inbredset_id>/names", methods=["GET"])
def inbredset_case_attribute_names(inbredset_id: int) -> Response:
    """Retrieve ALL case-attributes for a specific InbredSet group."""
    with (database_connection(current_app.config["SQL_URI"]) as conn,
          conn.cursor(cursorclass=DictCursor) as cursor):
        cursor.execute(
            "SELECT * FROM CaseAttribute WHERE InbredSetId=%(inbredset_id)s",
            {"inbredset_id": inbredset_id})
        return jsonify(tuple(dict(row) for row in cursor.fetchall()))

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

def __case_attributes_by_inbred_set__(
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
        return jsonify(__case_attributes_by_inbred_set__(conn, inbredset_id))

def __process_edit_data__(form_data) -> tuple[dict, ...]:
    """Process data from form and return tuple of dicts."""
    raise NotImplementedError

def __compute_diff__(original_data: tuple[dict, ...], edit_data: tuple[dict, ...]):
    """Return the diff of the data."""
    raise NotImplementedError

def __queue_diff__(conn: Connection, user: User, diff) -> str:
    """
    Queue diff for future processing.

    Returns: `diff`
        On success, this will return the filename where the diff was saved.
        On failure, it will raise a MySQL error.
    """
    # TODO: Check user has "edit case attribute privileges"
    raise NotImplementedError

def __apply_diff__(conn: Connection, user: User, diff_filename) -> None:
    """
    Apply the changes in the diff at `diff_filename` to the data in the database
    if the user has appropriate privileges.
    """
    # TODO: Check user has "approve/reject case attribute diff privileges"
    def __save_diff__(conn: Connection, diff_filename):
        """Save to the database."""
        raise NotImplementedError
    raise NotImplementedError

def __reject_diff__(conn: Connection, user: User, diff_filename) -> None:
    """
    Reject the changes in the diff at `diff_filename` to the data in the
    database if the user has appropriate privileges.
    """
    # TODO: Check user has "approve/reject case attribute diff privileges"
    raise NotImplementedError

@caseattr.route("/<int:inbredset_id>/add", methods=["POST"])
def add_case_attributes(inbredset_id: int) -> Response:
    """Add a new case attribute for `InbredSetId`."""
    with (require_oauth.acquire("profile resource") as the_token,
          database_connection(current_app.config["SQL_URI"]) as conn):
        # TODO: Check user has "add/delete case attribute privileges."
        raise NotImplementedError

@caseattr.route("/<int:inbredset_id>/delete", methods=["POST"])
def delete_case_attributes(inbredset_id: int) -> Response:
    """Delete a case attribute from `InbredSetId`."""
    with (require_oauth.acquire("profile resource") as the_token,
          database_connection(current_app.config["SQL_URI"]) as conn):
        # TODO: Check user has "add/delete case attribute privileges."
        raise NotImplementedError

@caseattr.route("/<int:inbredset_id>/edit", methods=["POST"])
def edit_case_attributes(inbredset_id: int) -> Response:
    """Edit the case attributes for `InbredSetId` based on data received."""
    with (require_oauth.acquire("profile resource") as the_token,
          database_connection(current_app.config["SQL_URI"]) as conn):
        # TODO: Check user has "edit case attribute privileges"
        user = the_token.user
        diff_filename = __queue_diff__(conn, user, __compute_diff__(
            __case_attributes_by_inbred_set__(conn, inbredset_id)
            __process_edit_data__(request.form)))
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
                "diff-filename": diff_filename
            })

@caseattr.route("/approve/<path:filename>", methods=["POST"])
def approve_case_attributes_diff(inbredset_id: int) -> Response:
    """Approve the changes to the case attributes in the diff."""
    # TODO: Check user has "approve/reject case attribute diff privileges"
    with (require_oauth.acquire("profile resource") as the_token,
          database_connection(current_app.config["SQL_URI"]) as conn):
        __apply_diff__(conn, the_token.user, diff_filename)
        raise NotImplementedError

@caseattr.route("/reject/<path:filename>", methods=["POST"])
def reject_case_attributes_diff(inbredset_id: int) -> Response:
    """Reject the changes to the case attributes in the diff."""
    # TODO: Check user has "approve/reject case attribute diff privileges"
    with (require_oauth.acquire("profile resource") as the_token,
          database_connection(current_app.config["SQL_URI"]) as conn):
        __reject_diff__(conn, the_token.user, diff_filename)
        raise NotImplementedError
