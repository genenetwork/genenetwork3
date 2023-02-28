"""Handle data endpoints."""
import uuid
import json

from authlib.integrations.flask_oauth2.errors import _HTTPException
from flask import request, jsonify, Response, Blueprint, current_app as app

from gn3.db.traits import build_trait_name

from gn3.auth import db
from gn3.auth.authentication.oauth2.resource_server import require_oauth
from gn3.auth.authorisation.resources.checks import authorised_for
from gn3.auth.authorisation.resources.models import (
    user_resources, public_resources, attach_resources_data)

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
