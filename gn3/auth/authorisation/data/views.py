"""Handle data endpoints."""
import uuid
import json

from email_validator import validate_email, EmailNotValidError
from authlib.integrations.flask_oauth2.errors import _HTTPException
from flask import request, jsonify, Response, Blueprint, current_app as app

from gn3.db.traits import build_trait_name

from gn3.auth import db
from gn3.auth.authorisation.users.views import validate_password
from gn3.auth.authorisation.resources.checks import authorised_for
from gn3.auth.authorisation.errors import ForbiddenAccess, AuthorisationError
from gn3.auth.authorisation.resources.models import (
    user_resources, public_resources, attach_resources_data)

from gn3.auth.authentication.oauth2.resource_server import require_oauth

data = Blueprint("data", __name__)

@data.route("/authorisation", methods=["GET"])
def authorisation() -> Response:
    """Retrive the authorisation level for datasets/traits for the user."""
    db_uri = app.config["AUTH_DB"]
    privileges = {}
    with db.connection(db_uri) as auth_conn:
        try:
            with require_oauth.acquire("profile group resource") as the_token:
                resources = attach_resources_data(
                    auth_conn, user_resources(auth_conn, the_token.user))
                privileges = {
                    resource_id: ("group:resource:view-resource",)
                    for resource_id, is_authorised
                    in authorised_for(
                        auth_conn, the_token.user,
                        ("group:resource:view-resource",), tuple(
                            resource.resource_id for resource in resources
                            if not resource.public)).items()
                    if is_authorised
                }
        except _HTTPException as exc:
            err_msg = json.loads(exc.body)
            if err_msg["error"] == "missing_authorization":
                resources = attach_resources_data(
                    auth_conn, public_resources(auth_conn))
            else:
                raise exc from None

        # Access endpoint with somethin like:
        # curl -X GET http://127.0.0.1:8080/api/oauth2/data/authorisation \
        #    -H "Content-Type: application/json" \
        #    -d '{"traits": ["HC_M2_0606_P::1442370_at", "BXDGeno::01.001.695",
        #        "BXDPublish::10001"]}'
        data_to_resource_map = {
            (f"{data_item['dataset_type'].lower()}::"
             f"{data_item['dataset_name']}"): resource.resource_id
            for resource in resources
            for data_item in resource.resource_data
        }
        privileges = {
            **privileges,
            **{
                resource.resource_id: ("system:resource:public-read",)
                for resource in resources if resource.public
            }}

        args = request.get_json()
        traits_names = args["traits"] # type: ignore[index]
        def __translate__(val):
            return {
                "ProbeSet": "mRNA",
                "Geno": "Genotype",
                "Publish": "Phenotype"
            }[val]
        return jsonify(tuple(
            {
                **{key:trait[key] for key in ("trait_fullname", "trait_name")},
                "dataset_name": trait["db"]["dataset_name"],
                "dataset_type": __translate__(trait["db"]["dataset_type"]),
                "privileges": privileges.get(
                    data_to_resource_map.get(
                        f"{__translate__(trait['db']['dataset_type']).lower()}"
                        f"::{trait['db']['dataset_name']}",
                        uuid.UUID("4afa415e-94cb-4189-b2c6-f9ce2b6a878d")),
                    tuple())
            } for trait in
            (build_trait_name(trait_fullname)
             for trait_fullname in traits_names)))

@data.route("/user/migrate", methods=["POST"])
@require_oauth("migrate-data")
def migrate_user_data():
    """
    Special, protected endpoint to enable the migration of data from the older
    system to the newer system with groups, resources and privileges.

    This is a temporary endpoint and should be removed after all the data has
    been migrated.
    """
    authorised_clients = app.config.get(
        "OAUTH2_CLIENTS_WITH_DATA_MIGRATION_PRIVILEGE", [])
    with require_oauth.acquire("migrate-data") as the_token:
        if the_token.client.client_id in authorised_clients:
            try:
                _user_id = uuid.UUID(request.form.get("user_id", ""))
                _email = validate_email(request.form.get("email", ""))
                _password = validate_password(
                    request.form.get("password", ""),
                    request.form.get("confirm_password", ""))
                ## TODO: Save the user: possible exception for duplicate emails
                ##       Create group from user's name
                ##       Filter all resources from redis owned by this user
                ##         resources = {key: json.loads(val)
                ##                      for key,val
                ##                      in rconn.hgetall("resources").items()}
                ##         filtered = dict((
                ##             (key,val) for key,val
                ##             in resources.items()
                ##             if uuid.UUID(val.get("owner_id")) == user_id))
                ##       Check that no resource is owned by existing user, use
                ##         'name' and 'type' fields to check in
                ##         `linked_group_data` table
                ##       Link remaining data to the new group
                ##       Delete user from redis
                return "WOULD TRIGGER DATA MIGRATION ..."
            except EmailNotValidError as enve:
                raise AuthorisationError(f"Email Error: {str(enve)}") from enve
            except ValueError as verr:
                raise AuthorisationError(verr.args[0]) from verr

        raise ForbiddenAccess("You cannot access this endpoint.")
