"""Implement case-attribute manipulations."""
from pathlib import Path

from functools import reduce
from urllib.parse import urljoin

import requests
from MySQLdb.cursors import DictCursor
from flask import (
    jsonify,
    make_response,
    request,
    url_for,
    Response,
    Blueprint,
    current_app)
from gn3.db.case_attributes import (
    CaseAttributeEdit,
    EditStatus,
    queue_edit,
    apply_change,
    get_changes)


from gn3.db_utils import Connection, database_connection

from gn_libs.privileges import resources

from gn3.oauth2.authorisation import require_token
from gn3.oauth2.errors import AuthorisationError

caseattr = Blueprint("case-attribute", __name__)
caseattrsbp = Blueprint("case-attributes", __name__)


@caseattr.after_request
def add_deprecation_headers(response):
    response.headers["Deprecation"] = "true"
    response.headers["Link"] = '</api/v1/>; rel="successor-version"'
    return response



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


# pylint: disable=[too-many-locals]
@caseattr.route("/<int:inbredset_id>/edit", methods=["POST"])
@require_token
def edit_case_attributes(inbredset_id: int, auth_token=None) -> tuple[Response, int]:
    """Edit the case attributes for `InbredSetId` based on data received.

    :inbredset_id: Identifier for the population that the case attribute belongs
    :auth_token: A validated JWT from the auth server
    """
    with database_connection(current_app.config["SQL_URI"]) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT SpeciesId FROM InbredSet WHERE InbredSetId=%s",
                (inbredset_id,))
            species_id = cursor.fetchone()[0]
        resource_privs, system_privs = __population_privileges__(
            auth_token, species_id, inbredset_id)
        if not resources.can_edit(resource_privs, system_privs):
            raise AuthorisationError(
                "You don't have the right privileges to edit this resource.")
    with database_connection(current_app.config["SQL_URI"]) as conn, conn.cursor() as cursor:
        data = request.json["edit-data"]  # type: ignore
        edit = CaseAttributeEdit(
            inbredset_id=inbredset_id,
            status=EditStatus.review,
            user_id=auth_token["jwt"]["sub"],
            changes=data
        )
        directory = (Path(current_app.config["LMDB_DATA_PATH"]) /
                     "case-attributes" / str(inbredset_id))
        queue_edit(cursor=cursor,
                   directory=directory,
                   edit=edit)
        return jsonify({
            "diff-status": "queued",
            "message": ("The changes to the case-attributes have been "
                        "queued for approval."),
        }), 201


@caseattr.route("/<int:inbredset_id>/diffs/<string:change_type>/list", methods=["GET"])
def list_diffs(inbredset_id: int, change_type: str) -> tuple[Response, int]:
    """List any changes that have been made by change_type."""
    with (database_connection(current_app.config["SQL_URI"]) as conn,
          conn.cursor(cursorclass=DictCursor) as cursor):
        directory = (Path(current_app.config["LMDB_DATA_PATH"]) /
                     "case-attributes" / str(inbredset_id))
        return jsonify(
            get_changes(
                cursor=cursor,
                change_type=EditStatus[change_type],
                directory=directory
            )
        ), 200


@caseattr.route("/<int:inbredset_id>/approve/<int:change_id>", methods=["POST"])
@require_token
def approve_case_attributes_diff(
        inbredset_id: int,
        change_id: int, auth_token=None
) -> tuple[Response, int]:
    """Approve the changes to the case attributes in the diff."""
    try:
        with database_connection(current_app.config["SQL_URI"]) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT SpeciesId FROM InbredSet WHERE InbredSetId=%s",
                    (inbredset_id,))
                species_id = cursor.fetchone()[0]
        resource_privs, system_privs = __population_privileges__(
            auth_token, species_id, inbredset_id)
        if not resources.can_apply_or_reject_edit(resource_privs, system_privs):
            raise AuthorisationError(
                "You don't have the right privileges to approve this edit.")
        with (database_connection(current_app.config["SQL_URI"]) as conn,
              conn.cursor() as cursor):
            directory = (Path(current_app.config["LMDB_DATA_PATH"]) /
                         "case-attributes" / str(inbredset_id))
            match apply_change(cursor, change_type=EditStatus.approved,
                               change_id=change_id,
                               directory=directory):
                case True:
                    return jsonify({
                        "diff-status": "approved",
                        "message": (f"Successfully approved # {change_id}")
                    }), 201
                case _:
                    return jsonify({
                        "diff-status": "queued",
                        "message": (f"Was not able to successfully approve # {change_id}")
                    }), 200
    except AuthorisationError as __auth_err:
        return jsonify({
            "diff-status": "queued",
            "message": "You don't have the right privileges to edit this resource."
        }), 401


@caseattr.route("/<int:inbredset_id>/reject/<int:change_id>", methods=["POST"])
@require_token
def reject_case_attributes_diff(
        inbredset_id: int, change_id: int, auth_token=None
) -> tuple[Response, int]:
    """Reject the changes to the case attributes in the diff."""
    try:
        with database_connection(current_app.config["SQL_URI"]) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT SpeciesId FROM InbredSet WHERE InbredSetId=%s",
                    (inbredset_id,))
                species_id = cursor.fetchone()[0]
        resource_privs, system_privs = __population_privileges__(
            auth_token, species_id, inbredset_id)
        if not resources.can_apply_or_reject_edit(resource_privs, system_privs):
            raise AuthorisationError(
                "You don't have the right privileges to reject this edit.")
        with database_connection(current_app.config["SQL_URI"]) as conn, \
                conn.cursor() as cursor:
            directory = (Path(current_app.config["LMDB_DATA_PATH"]) /
                         "case-attributes" / str(inbredset_id))
            match apply_change(cursor, change_type=EditStatus.rejected,
                               change_id=change_id,
                               directory=directory):
                case True:
                    return jsonify({
                        "diff-status": "rejected",
                        "message": ("The changes to the case-attributes have been "
                                    "rejected.")
                    }), 201
                case _:
                    return jsonify({
                        "diff-status": "queued",
                        "message": ("Failed to reject changes")
                    }), 200
    except AuthorisationError as __auth_err:
        return jsonify({
            "message": ("You don't have the right privileges to edit this resource.")
        }), 401


# ---------------------------------------------------------------------------
# v1 blueprint routes  (mounted at /api/v1/species/<s>/populations/<p>/case-attributes)
# Flask's blueprint nesting threads species_id and pop_id through to every
# child view function.
# ---------------------------------------------------------------------------

def __population_privileges__(
        auth_token: dict, species_id: int, pop_id: int
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return (resource_privs, system_privs) for the given population.

    species_id is taken from the URL — no DB lookup needed.
    Returns empty tuples for either set when the auth server reports an error,
    so privilege checks fail closed rather than open.
    """
    bearer = f"Bearer {auth_token['access_token']}"
    auth_url = current_app.config["AUTH_SERVER_URL"]

    resource_privs: tuple[str, ...] = tuple()
    res_id_resp = requests.get(
        urljoin(auth_url,
                f"auth/resource/populations/resource-id/{species_id}/{pop_id}"),
        timeout=300)
    if res_id_resp.status_code == 200:
        resource_id = res_id_resp.json()["resource-id"]
        roles_resp = requests.get(
            urljoin(auth_url, f"auth/resource/{resource_id}/roles"),
            headers={"Authorization": bearer},
            timeout=300)
        if roles_resp.status_code == 200:
            resource_privs = tuple(
                priv["privilege_id"]
                for role in roles_resp.json()
                for priv in role.get("privileges", []))

    system_privs: tuple[str, ...] = tuple()
    sys_resp = requests.get(
        urljoin(auth_url, "auth/resource/system/roles"),
        headers={"Authorization": bearer},
        timeout=300)
    if sys_resp.status_code == 200:
        system_privs = tuple(
            priv["privilege_id"]
            for role in sys_resp.json()
            for priv in role.get("privileges", []))

    return resource_privs, system_privs

@caseattrsbp.route("/", methods=["GET"])
def v1_list_case_attributes(species_id: int, pop_id: int) -> Response:
    """List all case-attribute names for the given population."""
    with database_connection(current_app.config["SQL_URI"]) as conn:
        data = __case_attribute_labels_by_inbred_set__(conn, pop_id)
    return jsonify({
        "data": data,
        "links": {
            "self": url_for(
                "v1.species.populations.case-attributes.v1_list_case_attributes",
                species_id=species_id, pop_id=pop_id),
            "edit": url_for(
                "v1.species.populations.case-attributes.v1_edit_case_attributes",
                species_id=species_id, pop_id=pop_id),
            "diffs": url_for(
                "v1.species.populations.case-attributes.v1_list_diffs",
                species_id=species_id, pop_id=pop_id, change_type="review"),
            "population": url_for(
                "v1.species.populations.population_details",
                species_id=species_id, pop_id=pop_id),
        }
    })


@caseattrsbp.route("/<int:ca_id>", methods=["GET"])
def v1_case_attribute_details(species_id: int, pop_id: int, ca_id: int) -> Response:
    return make_response(jsonify({
        "status": "not implemented",
        "message": "Single case-attribute details are not yet available."
    }), 501)


@caseattrsbp.route("/edit", methods=["POST"])
@require_token
def v1_edit_case_attributes(
        species_id: int, pop_id: int, auth_token=None) -> tuple[Response, int]:
    """Queue an edit to the case attributes for the given population."""
    resource_privs, system_privs = __population_privileges__(
        auth_token, species_id, pop_id)
    if not resources.can_edit(resource_privs, system_privs):
        raise AuthorisationError(
            "You don't have the right privileges to edit this resource.")
    with database_connection(current_app.config["SQL_URI"]) as conn, conn.cursor() as cursor:
        data = request.json["edit-data"]  # type: ignore
        edit = CaseAttributeEdit(
            inbredset_id=pop_id,
            status=EditStatus.review,
            user_id=auth_token["jwt"]["sub"],
            changes=data
        )
        directory = (Path(current_app.config["LMDB_DATA_PATH"]) /
                     "case-attributes" / str(pop_id))
        queue_edit(cursor=cursor, directory=directory, edit=edit)
        return jsonify({
            "diff-status": "queued",
            "message": ("The changes to the case-attributes have been "
                        "queued for approval."),
        }), 201


@caseattrsbp.route("/diffs/<string:change_type>/list", methods=["GET"])
def v1_list_diffs(
        species_id: int, pop_id: int, change_type: str) -> tuple[Response, int]:
    """List pending diffs for the given population by change type."""
    with (database_connection(current_app.config["SQL_URI"]) as conn,
          conn.cursor(cursorclass=DictCursor) as cursor):
        directory = (Path(current_app.config["LMDB_DATA_PATH"]) /
                     "case-attributes" / str(pop_id))
        return jsonify(
            get_changes(
                cursor=cursor,
                change_type=EditStatus[change_type],
                directory=directory
            )
        ), 200


@caseattrsbp.route("/diffs/<int:change_id>/approve", methods=["POST"])
@require_token
def v1_approve_case_attributes_diff(
        species_id: int, pop_id: int, change_id: int, auth_token=None
) -> tuple[Response, int]:
    """Approve a queued case-attribute diff."""
    try:
        resource_privs, system_privs = __population_privileges__(
            auth_token, species_id, pop_id)
        if not resources.can_apply_or_reject_edit(resource_privs, system_privs):
            raise AuthorisationError(
                "You don't have the right privileges to approve this edit.")
        with (database_connection(current_app.config["SQL_URI"]) as conn,
              conn.cursor() as cursor):
            directory = (Path(current_app.config["LMDB_DATA_PATH"]) /
                         "case-attributes" / str(pop_id))
            match apply_change(cursor, change_type=EditStatus.approved,
                               change_id=change_id, directory=directory):
                case True:
                    return jsonify({
                        "diff-status": "approved",
                        "message": f"Successfully approved # {change_id}"
                    }), 201
                case _:
                    return jsonify({
                        "diff-status": "queued",
                        "message": f"Was not able to successfully approve # {change_id}"
                    }), 200
    except AuthorisationError as __auth_err:
        return jsonify({
            "diff-status": "queued",
            "message": "You don't have the right privileges to edit this resource."
        }), 401


@caseattrsbp.route("/diffs/<int:change_id>/reject", methods=["POST"])
@require_token
def v1_reject_case_attributes_diff(
        species_id: int, pop_id: int, change_id: int, auth_token=None
) -> tuple[Response, int]:
    """Reject a queued case-attribute diff."""
    try:
        resource_privs, system_privs = __population_privileges__(
            auth_token, species_id, pop_id)
        if not resources.can_apply_or_reject_edit(resource_privs, system_privs):
            raise AuthorisationError(
                "You don't have the right privileges to reject this edit.")
        with database_connection(current_app.config["SQL_URI"]) as conn, \
                conn.cursor() as cursor:
            directory = (Path(current_app.config["LMDB_DATA_PATH"]) /
                         "case-attributes" / str(pop_id))
            match apply_change(cursor, change_type=EditStatus.rejected,
                               change_id=change_id, directory=directory):
                case True:
                    return jsonify({
                        "diff-status": "rejected",
                        "message": ("The changes to the case-attributes have been "
                                    "rejected.")
                    }), 201
                case _:
                    return jsonify({
                        "diff-status": "queued",
                        "message": "Failed to reject changes"
                    }), 200
    except AuthorisationError as __auth_err:
        return jsonify({
            "message": "You don't have the right privileges to edit this resource."
        }), 401
