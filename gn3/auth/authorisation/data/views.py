"""Handle data endpoints."""
import os
import uuid
import json
import random
import string
import datetime
from functools import reduce, partial
from typing import Any, Sequence, Iterable

import redis
from MySQLdb.cursors import DictCursor
from email_validator import validate_email, EmailNotValidError
from authlib.integrations.flask_oauth2.errors import _HTTPException
from flask import request, jsonify, Response, Blueprint, current_app as app

import gn3.db_utils as gn3db
from gn3.db.traits import build_trait_name

from gn3.auth import db
from gn3.auth.dictify import dictify
from gn3.auth.db_utils import with_db_connection

from gn3.auth.authorisation.errors import InvalidData, NotFoundError

from gn3.auth.authorisation.roles.models import(
    revoke_user_role_by_name, assign_user_role_by_name)

from gn3.auth.authorisation.groups.data import retrieve_ungrouped_data
from gn3.auth.authorisation.groups.models import (
    Group, user_group, group_by_id, add_user_to_group)

from gn3.auth.authorisation.resources.checks import authorised_for
from gn3.auth.authorisation.resources.models import (
    user_resources, public_resources, attach_resources_data)

from gn3.auth.authorisation.errors import ForbiddenAccess


from gn3.auth.authentication.oauth2.resource_server import require_oauth
from gn3.auth.authentication.users import User, user_by_email, set_user_password

from gn3.auth.authorisation.data.genotypes import (
    link_genotype_data, ungrouped_genotype_data)

data = Blueprint("data", __name__)

@data.route("species")
def list_species() -> Response:
    """List all available species information."""
    with (gn3db.database_connection() as gn3conn,
          gn3conn.cursor(DictCursor) as cursor):
        cursor.execute("SELECT * FROM Species")
        return jsonify(tuple(dict(row) for row in cursor.fetchall()))

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

def migrate_user_group(conn: db.DbConnection, user: User) -> Group:
    """Create a group for the user if they don't already have a group."""
    group = user_group(conn, user).maybe(# type: ignore[misc]
        False, lambda grp: grp) # type: ignore[arg-type]
    if not bool(group):
        now = datetime.datetime.now().isoformat()
        group = Group(uuid.uuid4(), f"{user.name}'s Group ({now})", {
            "created": now,
            "notes": "Imported from redis"
        })
        with db.cursor(conn) as cursor:
            cursor.execute(
                "INSERT INTO groups(group_id, group_name, group_metadata) "
                "VALUES(?, ?, ?)",
                (str(group.group_id), group.group_name, json.dumps(
                    group.group_metadata)))
            add_user_to_group(cursor, group, user)
            revoke_user_role_by_name(cursor, user, "group-creator")
            assign_user_role_by_name(cursor, user, "group-leader")

    return group

def __redis_datasets_by_type__(acc, item):
    if item["type"] == "dataset-probeset":
        return (acc[0] + (item["name"],), acc[1], acc[2])
    if item["type"] == "dataset-geno":
        return (acc[0], acc[1] + (item["name"],), acc[2])
    if item["type"] == "dataset-publish":
        return (acc[0], acc[1], acc[2] + (item["name"],))
    return acc

def __unmigrated_data__(ungrouped, redis_datasets):
    return (dataset for dataset in ungrouped
            if dataset["Name"] in redis_datasets)

def __parametrise__(group: Group, datasets: Sequence[dict],
                    dataset_type: str) -> tuple[dict[str, str], ...]:
    return tuple(
        {
            "group_id": str(group.group_id),
            "dataset_type": dataset_type,
            "dataset_or_trait_id": dataset["Id"],
            "dataset_name": dataset["Name"],
            "dataset_fullname": dataset["FullName"],
            "accession_id": dataset["accession_id"]
        } for dataset in datasets)

def __org_by_user_id__(acc, resource):
    try:
        user_id = uuid.UUID(resource["owner_id"])
        return {
            **acc,
            user_id: acc.get(user_id, tuple()) + (resource,)
        }
    except ValueError as _verr:
        return acc

def redis_resources(rconn: redis.Redis) -> Iterable[dict[str, str]]:
    """Retrieve ALL defined resources from Redis"""
    return (
        json.loads(resource)
        for resource in rconn.hgetall("resources").values())

def system_admin_user(conn: db.DbConnection) -> User:
    """Return a system admin user."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "SELECT * FROM users AS u INNER JOIN user_roles AS ur "
            "ON u.user_id=ur.user_id INNER JOIN roles AS r "
            "ON ur.role_id=r.role_id WHERE r.role_name='system-administrator'")
        rows = cursor.fetchall()
        if len(rows) > 0:
            return User(uuid.UUID(rows[0]["user_id"]), rows[0]["email"],
                        rows[0]["name"])
        raise NotFoundError("Could not find a system administration user.")

def migrate_user(
        conn: db.DbConnection, email: str, username: str, password: str) -> User:
    """Migrate the user, if not already migrated."""
    try:
        return user_by_email(conn, email)
    except NotFoundError as _nfe:
        user = User(uuid.uuid4(), email, username)
        with db.cursor(conn) as cursor:
            cursor.execute(
                "INSERT INTO users(user_id, email, name) "
                "VALUES (?, ?, ?)",
                (str(user.user_id), user.email, user.name))
            set_user_password(cursor, user, password)
            return user

def __generate_random_password__(length: int = 25):
    """Generate a random password string"""
    return "".join(random.choices(
        string.ascii_letters + string.punctuation + string.digits,
        k=length))

def migrate_data(# pylint: disable=[too-many-locals]
        authconn: db.DbConnection,
        gn3conn: gn3db.Connection,
        rconn: redis.Redis,
        redis_user_id: uuid.UUID,
        redisresources: tuple[dict[str, str], ...]) -> tuple[
            User, Group, tuple[dict[str, str], ...]]:
    """Migrate data attached to the user to the user's group."""
    try:
        user_details = json.loads(rconn.hget("users", str(redis_user_id)))
        email = validate_email(user_details["email_address"])
        user = migrate_user(authconn, email["email"],
                            user_details.get("full_name") or "NOT SET",
                            __generate_random_password__())
        group = migrate_user_group(authconn, user)
        redis_mrna, redis_geno, redis_pheno = reduce(#type: ignore[var-annotated]
            __redis_datasets_by_type__, redisresources,
            (tuple(), tuple(), tuple()))
        mrna_datasets = __unmigrated_data__(
            retrieve_ungrouped_data(authconn, gn3conn, "mrna"), redis_mrna)
        geno_datasets = __unmigrated_data__(
            retrieve_ungrouped_data(authconn, gn3conn, "genotype"), redis_geno)
        pheno_datasets = __unmigrated_data__(
            retrieve_ungrouped_data(authconn, gn3conn, "phenotype"), redis_pheno)

        params = (
            __parametrise__(group, mrna_datasets, "mRNA") +
            __parametrise__(group, geno_datasets, "Genotype") +
            __parametrise__(group, pheno_datasets, "Phenotype"))
        if len(params) > 0:
            with db.cursor(authconn) as cursor:
                cursor.executemany(
                    "INSERT INTO linked_group_data VALUES"
                    "(:group_id, :dataset_type, :dataset_or_trait_id, "
                    ":dataset_name, :dataset_fullname, :accession_id)",
                    params)

        return user, group, params
    except EmailNotValidError as _enve:
        pass

    return tuple() # type: ignore[return-value]

@data.route("/users/migrate", methods=["POST"])
@require_oauth("migrate-data")
def migrate_users_data() -> Response:
    """
    Special, protected endpoint to enable the migration of data from the older
    system to the newer system with groups, resources and privileges.

    This is a temporary endpoint and should be removed after all the data has
    been migrated.
    """
    db_uri = app.config.get("AUTH_DB", "").strip()
    if bool(db_uri) and os.path.exists(db_uri):
        authorised_clients = app.config.get(
            "OAUTH2_CLIENTS_WITH_DATA_MIGRATION_PRIVILEGE", [])
        with (require_oauth.acquire("migrate-data") as the_token,
              db.connection(db_uri) as authconn,
              redis.Redis(decode_responses=True) as rconn,
              gn3db.database_connection() as gn3conn):
            if the_token.client.client_id in authorised_clients:
                by_user: dict[uuid.UUID, tuple[dict[str, str], ...]] = reduce(
                    __org_by_user_id__, redis_resources(rconn), {})
                users, groups, resource_data_params = reduce(# type: ignore[var-annotated, arg-type]
                    lambda acc, ugp: (acc[0] + (ugp[0],),# type: ignore[return-value, arg-type]
                                      acc[1] + (ugp[1],),
                                      acc[2] + ugp[2]),
                    (
                    migrate_data(
                        authconn, gn3conn, rconn, user_id, user_resources)
                        for user_id, user_resources in by_user.items()),
                    (tuple(), tuple(), tuple()))
                return jsonify({
                    "description": (
                        f"Migrated {len(resource_data_params)} resource data "
                        f"items for {len(users)} users into {len(groups)} "
                        "groups."),
                    "users": tuple(dictify(user) for user in users),
                    "groups": tuple(dictify(group) for group in groups)
                })
            raise ForbiddenAccess("You cannot access this endpoint.")

    return app.response_class(
        response=json.dumps({
            "error": "Unavailable",
            "error_description": (
                "The data migration service is currently unavailable.")
        }),
        status=500, mimetype="application/json")

def __search_mrna__():
    pass

def __search_genotypes__():
    query = request.form.get("query", request.args.get("query", ""))
    limit = int(request.form.get("limit", request.args.get("limit", 10000)))
    offset = int(request.form.get("offset", request.args.get("offset", 0)))
    with gn3db.database_connection() as gn3conn:
        __ungrouped__ = partial(
            ungrouped_genotype_data, gn3conn=gn3conn, search_query=query,
            limit=limit, offset=offset)
        return jsonify(with_db_connection(__ungrouped__))

def __search_phenotypes__():
    pass

@data.route("/search", methods=["GET"])
@require_oauth("profile group resource")
def search_unlinked_data():
    """Search for various unlinked data."""
    dataset_type = request.form["dataset_type"]
    search_fns = {
        "mrna": __search_mrna__,
        "genotype": __search_genotypes__,
        "phenotype": __search_phenotypes__
    }
    return search_fns[dataset_type]()

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
        if not bool(form.get("selected_datasets")):
            raise InvalidData("Expected at least one dataset to be provided.")
        return {
            "group_id": uuid.UUID(form.get("group_id")),
            "datasets": form.get("selected_datasets")
        }

    def __link__(conn: db.DbConnection, group_id: uuid.UUID, datasets: dict):
        return link_genotype_data(conn, group_by_id(conn, group_id), datasets)

    return jsonify(with_db_connection(
        partial(__link__, **__values__(request.json))))
