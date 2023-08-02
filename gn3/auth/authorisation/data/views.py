"""Handle data endpoints."""
import sys
import uuid
import json
from typing import Any
from functools import partial

import redis
from MySQLdb.cursors import DictCursor
from authlib.integrations.flask_oauth2.errors import _HTTPException
from flask import request, jsonify, Response, Blueprint, current_app as app

import gn3.db_utils as gn3db
from gn3 import jobs
from gn3.commands import run_async_cmd
from gn3.db.traits import build_trait_name

from gn3.auth import db
from gn3.auth.db_utils import with_db_connection

from gn3.auth.authorisation.checks import require_json
from gn3.auth.authorisation.errors import InvalidData, NotFoundError

from gn3.auth.authorisation.groups.models import group_by_id

from gn3.auth.authorisation.users.models import user_resource_roles

from gn3.auth.authorisation.resources.checks import authorised_for
from gn3.auth.authorisation.resources.models import (
    user_resources, public_resources, attach_resources_data)

from gn3.auth.authentication.users import User
from gn3.auth.authentication.oauth2.resource_server import require_oauth

from gn3.auth.authorisation.data.phenotypes import link_phenotype_data
from gn3.auth.authorisation.data.mrna import link_mrna_data, ungrouped_mrna_data
from gn3.auth.authorisation.data.genotypes import (
    link_genotype_data, ungrouped_genotype_data)

data = Blueprint("data", __name__)

@data.route("species")
def list_species() -> Response:
    """List all available species information."""
    with (gn3db.database_connection(app.config["SQL_URI"]) as gn3conn,
          gn3conn.cursor(DictCursor) as cursor):
        cursor.execute("SELECT * FROM Species")
        return jsonify(tuple(dict(row) for row in cursor.fetchall()))

@data.route("/authorisation", methods=["POST"])
@require_json
def authorisation() -> Response:
    """Retrive the authorisation level for datasets/traits for the user."""
    # Access endpoint with something like:
    # curl -X POST http://127.0.0.1:8080/api/oauth2/data/authorisation \
    #    -H "Content-Type: application/json" \
    #    -d '{"traits": ["HC_M2_0606_P::1442370_at", "BXDGeno::01.001.695",
    #        "BXDPublish::10001"]}'
    db_uri = app.config["AUTH_DB"]
    privileges = {}
    user = User(uuid.uuid4(), "anon@ymous.user", "Anonymous User")
    with db.connection(db_uri) as auth_conn:
        try:
            with require_oauth.acquire("profile group resource") as the_token:
                user = the_token.user
                resources = attach_resources_data(
                    auth_conn, user_resources(auth_conn, the_token.user))
                resources_roles = user_resource_roles(auth_conn, the_token.user)
                privileges = {
                    resource_id: tuple(
                        privilege.privilege_id
                        for roles in resources_roles[resource_id]
                        for privilege in roles.privileges)#("group:resource:view-resource",)
                    for resource_id, is_authorised
                    in authorised_for(
                        auth_conn, the_token.user,
                        ("group:resource:view-resource",), tuple(
                            resource.resource_id for resource in resources)).items()
                    if is_authorised
                }
        except _HTTPException as exc:
            err_msg = json.loads(exc.body)
            if err_msg["error"] == "missing_authorization":
                resources = attach_resources_data(
                    auth_conn, public_resources(auth_conn))
            else:
                raise exc from None

        def __gen_key__(resource, data_item):
            if resource.resource_category.resource_category_key.lower() == "phenotype":
                return (
                    f"{resource.resource_category.resource_category_key.lower()}::"
                    f"{data_item['dataset_name']}::{data_item['PublishXRefId']}")
            return (
                f"{resource.resource_category.resource_category_key.lower()}::"
                f"{data_item['dataset_name']}")

        data_to_resource_map = {
            __gen_key__(resource, data_item): resource.resource_id
            for resource in resources
            for data_item in resource.resource_data
        }
        privileges = {
            **{
                resource.resource_id: ("system:resource:public-read",)
                for resource in resources if resource.public
            },
            **privileges}

        args = request.get_json()
        traits_names = args["traits"] # type: ignore[index]
        def __translate__(val):
            return {
                "Temp": "Temp",
                "ProbeSet": "mRNA",
                "Geno": "Genotype",
                "Publish": "Phenotype"
            }[val]

        def __trait_key__(trait):
            dataset_type = __translate__(trait['db']['dataset_type']).lower()
            dataset_name = trait["db"]["dataset_name"]
            if dataset_type == "phenotype":
                return f"{dataset_type}::{dataset_name}::{trait['trait_name']}"
            return f"{dataset_type}::{dataset_name}"

        return jsonify(tuple(
            {
                "user": user._asdict(),
                **{key:trait[key] for key in ("trait_fullname", "trait_name")},
                "dataset_name": trait["db"]["dataset_name"],
                "dataset_type": __translate__(trait["db"]["dataset_type"]),
                "resource_id": data_to_resource_map.get(__trait_key__(trait)),
                "privileges": privileges.get(
                    data_to_resource_map.get(
                        __trait_key__(trait),
                        uuid.UUID("4afa415e-94cb-4189-b2c6-f9ce2b6a878d")),
                    tuple()) + (
                        # Temporary traits do not exist in db: Set them
                        # as public-read
                        ("system:resource:public-read",)
                        if trait["db"]["dataset_type"] == "Temp"
                        else tuple())
            } for trait in
            (build_trait_name(trait_fullname)
             for trait_fullname in traits_names)))

def __search_mrna__():
    query = __request_key__("query", "")
    limit = int(__request_key__("limit", 10000))
    offset = int(__request_key__("offset", 0))
    with gn3db.database_connection(app.config["SQL_URI"]) as gn3conn:
        __ungrouped__ = partial(
            ungrouped_mrna_data, gn3conn=gn3conn, search_query=query,
            selected=__request_key_list__("selected"),
            limit=limit, offset=offset)
        return jsonify(with_db_connection(__ungrouped__))

def __request_key__(key: str, default: Any = ""):
    if bool(request.json):
        return request.json.get(#type: ignore[union-attr]
            key, request.args.get(key, request.form.get(key, default)))
    return request.args.get(key, request.form.get(key, default))

def __request_key_list__(key: str, default: tuple[Any, ...] = tuple()):
    if bool(request.json):
        return (request.json.get(key,[])#type: ignore[union-attr]
                or request.args.getlist(key) or request.form.getlist(key)
                or list(default))
    return (request.args.getlist(key)
            or request.form.getlist(key) or list(default))

def __search_genotypes__():
    query = __request_key__("query", "")
    limit = int(__request_key__("limit", 10000))
    offset = int(__request_key__("offset", 0))
    with gn3db.database_connection(app.config["SQL_URI"]) as gn3conn:
        __ungrouped__ = partial(
            ungrouped_genotype_data, gn3conn=gn3conn, search_query=query,
            selected=__request_key_list__("selected"),
            limit=limit, offset=offset)
        return jsonify(with_db_connection(__ungrouped__))

def __search_phenotypes__():
    # launch the external process to search for phenotypes
    redisuri = app.config["REDIS_URI"]
    with redis.Redis.from_url(redisuri, decode_responses=True) as redisconn:
        job_id = uuid.uuid4()
        selected = __request_key__("selected_traits", [])
        command =[
            sys.executable, "-m", "scripts.search_phenotypes",
            __request_key__("species_name"),
            __request_key__("query"),
            str(job_id),
            f"--host={__request_key__('gn3_server_uri')}",
            f"--auth-db-uri={app.config['AUTH_DB']}",
            f"--gn3-db-uri={app.config['SQL_URI']}",
            f"--redis-uri={redisuri}",
            f"--per-page={__request_key__('per_page')}"] +(
                [f"--selected={json.dumps(selected)}"]
                if len(selected) > 0 else [])
        jobs.create_job(redisconn, {
            "job_id": job_id, "command": command, "status": "queued",
            "search_results": tuple()})
        return jsonify({
            "job_id": job_id,
            "command_id": run_async_cmd(
                redisconn, app.config.get("REDIS_JOB_QUEUE"), command),
            "command": command
        })

@data.route("/search", methods=["GET"])
@require_oauth("profile group resource")
def search_unlinked_data():
    """Search for various unlinked data."""
    dataset_type = request.json["dataset_type"]
    search_fns = {
        "mrna": __search_mrna__,
        "genotype": __search_genotypes__,
        "phenotype": __search_phenotypes__
    }
    return search_fns[dataset_type]()

@data.route("/search/phenotype/<uuid:job_id>", methods=["GET"])
def pheno_search_results(job_id: uuid.UUID) -> Response:
    """Get the search results from the external script"""
    def __search_error__(err):
        raise NotFoundError(err["error_description"])
    redisuri = app.config["REDIS_URI"]
    with redis.Redis.from_url(redisuri, decode_responses=True) as redisconn:
        return jobs.job(redisconn, job_id).either(
            __search_error__, jsonify)

@data.route("/link/genotype", methods=["POST"])
def link_genotypes() -> Response:
    """Link genotype data to group."""
    def __values__(form) -> dict[str, Any]:
        if not bool(form.get("species_name", "").strip()):
            raise InvalidData("Expected 'species_name' not provided.")
        if not bool(form.get("group_id")):
            raise InvalidData("Expected 'group_id' not provided.",)
        try:
            _group_id = uuid.UUID(form.get("group_id"))
        except TypeError as terr:
            raise InvalidData("Expected a UUID for 'group_id' value.") from terr
        if not bool(form.get("selected")):
            raise InvalidData("Expected at least one dataset to be provided.")
        return {
            "group_id": uuid.UUID(form.get("group_id")),
            "datasets": form.get("selected")
        }

    def __link__(conn: db.DbConnection, group_id: uuid.UUID, datasets: dict):
        return link_genotype_data(conn, group_by_id(conn, group_id), datasets)

    return jsonify(with_db_connection(
        partial(__link__, **__values__(request.json))))

@data.route("/link/mrna", methods=["POST"])
def link_mrna() -> Response:
    """Link mrna data to group."""
    def __values__(form) -> dict[str, Any]:
        if not bool(form.get("species_name", "").strip()):
            raise InvalidData("Expected 'species_name' not provided.")
        if not bool(form.get("group_id")):
            raise InvalidData("Expected 'group_id' not provided.",)
        try:
            _group_id = uuid.UUID(form.get("group_id"))
        except TypeError as terr:
            raise InvalidData("Expected a UUID for 'group_id' value.") from terr
        if not bool(form.get("selected")):
            raise InvalidData("Expected at least one dataset to be provided.")
        return {
            "group_id": uuid.UUID(form.get("group_id")),
            "datasets": form.get("selected")
        }

    def __link__(conn: db.DbConnection, group_id: uuid.UUID, datasets: dict):
        return link_mrna_data(conn, group_by_id(conn, group_id), datasets)

    return jsonify(with_db_connection(
        partial(__link__, **__values__(request.json))))

@data.route("/link/phenotype", methods=["POST"])
def link_phenotype() -> Response:
    """Link phenotype data to group."""
    def __values__(form):
        if not bool(form.get("species_name", "").strip()):
            raise InvalidData("Expected 'species_name' not provided.")
        if not bool(form.get("group_id")):
            raise InvalidData("Expected 'group_id' not provided.",)
        try:
            _group_id = uuid.UUID(form.get("group_id"))
        except TypeError as terr:
            raise InvalidData("Expected a UUID for 'group_id' value.") from terr
        if not bool(form.get("selected")):
            raise InvalidData("Expected at least one dataset to be provided.")
        return {
            "group_id": uuid.UUID(form["group_id"]),
            "traits": form["selected"]
        }

    with gn3db.database_connection(app.config["SQL_URI"]) as gn3conn:
        def __link__(conn: db.DbConnection, group_id: uuid.UUID,
                     traits: tuple[dict, ...]) -> dict:
            return link_phenotype_data(
                conn, gn3conn, group_by_id(conn, group_id), traits)

        return jsonify(with_db_connection(
            partial(__link__, **__values__(request.json))))
