"""Handle data endpoints."""
import json
from functools import reduce

from flask import request, Response, Blueprint, current_app as app
from authlib.integrations.flask_oauth2.errors import _HTTPException

from gn3 import db_utils as gn3db

from gn3.db.traits import build_trait_name

from gn3.auth import db
from gn3.auth.authentication.oauth2.resource_server import require_oauth
from gn3.auth.authorisation.resources.models import (
    user_resources, public_resources, attach_resources_data)

data = Blueprint("data", __name__)

@data.route("/authorisation", methods=["GET"])
def authorisation() -> Response:
    """Retrive the authorisation level for datasets/traits for the user."""
    db_uri = app.config["AUTH_DB"]
    the_user = "ANONYMOUS"
    with db.connection(db_uri) as auth_conn, gn3db.database_connection() as gn3conn:
        try:
            with require_oauth.acquire("profile group resource") as the_token:
                resources = attach_resources_data(
                    auth_conn, user_resources(auth_conn, the_token.user))
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
        #    -d '{"traits": ["HC_M2_0606_P::1442370_at", "BXDGeno::01.001.695", "BXDPublish::10001"]}'
        args = request.get_json()
        traits_names = args["traits"]
        def __translate__(val):
            return {
                "ProbeSet": "mRNA",
                "Geno": "Genotype",
                "Publish": "Phenotype"
            }[val]
        traits = (
            {
                **{key:trait[key] for key in ("trait_fullname", "trait_name")},
                "dataset_name": trait["db"]["dataset_name"],
                "dataset_type": __translate__(trait["db"]["dataset_type"])
            } for trait in
            (build_trait_name(trait_fullname)
             for trait_fullname in traits_names))
        # Retrieve the dataset/trait IDs from traits above

        # Compare the traits/dataset names/ids from request with resources' data
        # - Any trait not in resources' data is marked inaccessible
        # - Any trait in resources' data:
        #   - IF public is marked readable
        #   - IF private and user has read privilege: mark readable
        #   - ELSE mark inaccessible
        

        return "NOT COMPLETED! ..."
