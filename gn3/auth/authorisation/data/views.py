"""Handle data endpoints."""
import os
import uuid
import json
import datetime
from typing import Sequence
from functools import reduce

import redis
from email_validator import validate_email, EmailNotValidError
from authlib.integrations.flask_oauth2.errors import _HTTPException
from flask import request, jsonify, Response, Blueprint, current_app as app

import gn3.db_utils as gn3db
from gn3.db.traits import build_trait_name

from gn3.auth import db
from gn3.auth.dictify import dictify

from gn3.auth.authorisation.errors import NotFoundError

from gn3.auth.authorisation.users.views import (
    validate_password, validate_username)

from gn3.auth.authorisation.roles.models import(
    revoke_user_role_by_name, assign_user_role_by_name)

from gn3.auth.authorisation.groups.data import retrieve_ungrouped_data
from gn3.auth.authorisation.groups.models import (
    Group, user_group, add_user_to_group)

from gn3.auth.authorisation.resources.checks import authorised_for
from gn3.auth.authorisation.resources.models import (
    user_resources, public_resources, attach_resources_data)

from gn3.auth.authorisation.errors import ForbiddenAccess, AuthorisationError


from gn3.auth.authentication.oauth2.resource_server import require_oauth
from gn3.auth.authentication.users import User, user_by_id, set_user_password
from gn3.auth.authentication.oauth2.models.oauth2token import (
    OAuth2Token, save_token)
from gn3.auth.authentication.oauth2.models.oauth2client import (
    client_by_id_and_secret)

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

def migrate_user_group(conn: db.DbConnection, user: User) -> Group:
    """Create a group for the user if they don't already have a group."""
    group = user_group(conn, user).maybe(# type: ignore[misc]
        False, lambda grp: grp) # type: ignore[arg-type]
    if not bool(group):
        group = Group(uuid.uuid4(), f"{user.name}'s Group", {
            "created": datetime.datetime.now().isoformat(),
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

def user_redis_resources(rconn: redis.Redis, user_id: uuid.UUID) -> tuple[
        tuple[dict], tuple[dict], tuple[dict]]:
    """Acquire any resources from redis."""
    return reduce(# type: ignore[var-annotated]
        __redis_datasets_by_type__,
        (dataset for dataset in
         (dataset for _key,dataset in {
             key: json.loads(val)
            for key,val in rconn.hgetall("resources").items()
         }.items())
         if dataset["owner_id"] == str(user_id)),
        (tuple(), tuple(), tuple()))

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

def generate_sysadmin_token() -> OAuth2Token:
    """Generate a token for a user with system administration privileges."""
    db_uri = app.config["AUTH_DB"]
    server = app.config["OAUTH2_SERVER"]
    with (require_oauth.acquire("profile") as the_token,
          db.connection(db_uri) as conn):
        admin_user = system_admin_user(conn)
        token = OAuth2Token(
            token_id = uuid.uuid4(),
            client = the_token.client,
            **server.generate_token(
            client = the_token.client,
            grant_type = "implicit",
            user = admin_user,
            scope = the_token.scope,
            expires_in = 30*60,
                include_refresh_token=False),
            refresh_token = None,
            revoked=False,
            issued_at=datetime.datetime.now(),
            user=admin_user)
        save_token(conn, token)
        return token

def migrate_data(
        authconn: db.DbConnection, gn3conn: gn3db.Connection,
        redis_resources: tuple[tuple[dict], tuple[dict], tuple[dict]],
        user: User, group: Group) -> tuple[dict[str, str], ...]:
    """Migrate data attached to the user to the user's group."""
    redis_mrna, redis_geno, redis_pheno = redis_resources
    ## BEGIN: Escalate privileges temporarily to enable fetching of data
    ## =====================================
    new_token = generate_sysadmin_token()
    with app.test_request_context(headers={
            "Authorization": f"Bearer {new_token.access_token}"}):
        mrna_datasets = __unmigrated_data__(
            retrieve_ungrouped_data(authconn, gn3conn, "mrna"), redis_mrna)
        geno_datasets = __unmigrated_data__(
            retrieve_ungrouped_data(authconn, gn3conn, "genotype"), redis_geno)
        pheno_datasets = __unmigrated_data__(
            retrieve_ungrouped_data(authconn, gn3conn, "phenotype"), redis_pheno)
    ## =====================================
    ## END: Escalate privileges temporarily to enable fetching of data

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

    return params

@data.route("/user/migrate", methods=["POST"])
# @require_oauth("migrate-data")
def migrate_user() -> Response:
    """Migrate the user"""
    def __migrate_user__(conn: db.DbConnection, user_id: uuid.UUID, email: str,
                 username: str, password: str) -> User:
        """Migrate the user, if not already migrated."""
        try:
            return user_by_id(conn, user_id)
        except NotFoundError as _nfe:
            user = User(user_id, email, username)
            with db.cursor(conn) as cursor:
                cursor.execute(
                    "INSERT INTO users(user_id, email, name) "
                    "VALUES (?, ?, ?)",
                    (str(user.user_id), user.email, user.name))
                set_user_password(cursor, user, password)
                return user
    try:
        db_uri = app.config.get("AUTH_DB").strip()
        with (db.connection(db_uri) as authconn,
              redis.Redis(decode_responses=True) as rconn):
            client_id = uuid.UUID(request.form.get("client_id"))
            client_secret = request.form.get("client_secret", "NOTASECRET")
            client = client_by_id_and_secret(authconn, client_id, client_secret)
            authorised_clients = app.config.get(
                "OAUTH2_CLIENTS_WITH_DATA_MIGRATION_PRIVILEGE", [])
            if client.client_id not in  authorised_clients:
                raise ForbiddenAccess("You cannot access this endpoint.")

            user_id = uuid.UUID(request.form.get("user_id"))
            redis_dets = rconn.hget("users", str(user_id))
            user_details = json.loads(redis_dets)
            if user_details:
                email = validate_email(user_details["email_address"])
                user = __migrate_user__(
                    authconn, user_id, email["email"],
                    validate_username(user_details.get("full_name", "")),
                    validate_password(
                        request.form.get("password", ""),
                        request.form.get("confirm_password", "")))
                return jsonify({
                    "user": dictify(user),
                    "description": "Successfully migrated user."
                })
            raise NotFoundError(
                f"No user with ID '{user_id}'")
    except EmailNotValidError as enve:
        raise AuthorisationError(f"Email Error: {str(enve)}") from enve
    except ValueError as verr:
        raise AuthorisationError(verr.args[0]) from verr

@data.route("/user/<uuid:user_id>/migrate", methods=["POST"])
@require_oauth("migrate-data")
def migrate_user_data(user_id: uuid.UUID) -> Response:
    """
    Special, protected endpoint to enable the migration of data from the older
    system to the newer system with groups, resources and privileges.

    This is a temporary endpoint and should be removed after all the data has
    been migrated.
    """
    db_uri = app.config.get("AUTH_DB").strip()
    if bool(db_uri) and os.path.exists(db_uri):
        authorised_clients = app.config.get(
            "OAUTH2_CLIENTS_WITH_DATA_MIGRATION_PRIVILEGE", [])
        with require_oauth.acquire("migrate-data") as the_token:
            if the_token.client.client_id in authorised_clients:
                user = the_token.user
                with (db.connection(db_uri) as authconn,
                      redis.Redis(decode_responses=True) as rconn,
                      gn3db.database_connection() as gn3conn):
                    redis_resources = user_redis_resources(rconn, user.user_id)
                    user_resource_data = tuple()
                    if any(bool(item) for item in redis_resources):
                        group = migrate_user_group(authconn, user)
                        user_resource_data = migrate_data(
                            authconn, gn3conn, redis_resources, user, group)
                        ## TODO: Maybe delete user from redis...
                    return jsonify({
                        "description": (
                            f"Migrated {len(user_resource_data)} resource data "
                            "items."),
                        "user": dictify(user),
                        "group": dictify(group)
                    })

            raise ForbiddenAccess("You cannot access this endpoint.")

    return jsonify({
        "error": "Unavailable",
        "error_description": (
            "The data migration service is currently unavailable.")
    }), 503
