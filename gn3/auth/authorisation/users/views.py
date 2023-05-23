"""User authorisation endpoints."""
import traceback
from typing import Any
from functools import partial

import sqlite3
from email_validator import validate_email, EmailNotValidError
from flask import request, jsonify, Response, Blueprint, current_app

from gn3.auth import db
from gn3.auth.dictify import dictify
from gn3.auth.db_utils import with_db_connection

from .models import list_users
from .masquerade.views import masq
from .collections.views import collections

from ..groups.models import user_group as _user_group
from ..resources.models import user_resources as _user_resources
from ..roles.models import assign_default_roles, user_roles as _user_roles
from ..errors import (
    NotFoundError, UsernameError, PasswordError, UserRegistrationError)

from ...authentication.oauth2.resource_server import require_oauth
from ...authentication.users import User, save_user, set_user_password
from ...authentication.oauth2.models.oauth2token import token_by_access_token

users = Blueprint("users", __name__)
users.register_blueprint(masq, url_prefix="/masquerade")
users.register_blueprint(collections, url_prefix="/collections")

@users.route("/", methods=["GET"])
@require_oauth("profile")
def user_details() -> Response:
    """Return user's details."""
    with require_oauth.acquire("profile") as the_token:
        user = the_token.user
        user_dets = {
            "user_id": user.user_id, "email": user.email, "name": user.name,
            "group": False
        }
        with db.connection(current_app.config["AUTH_DB"]) as conn:
            the_group = _user_group(conn, user).maybe(# type: ignore[misc]
                False, lambda grp: grp)# type: ignore[arg-type]
            return jsonify({
                **user_dets,
                "group": dictify(the_group) if the_group else False
            })

@users.route("/roles", methods=["GET"])
@require_oauth("role")
def user_roles() -> Response:
    """Return the non-resource roles assigned to the user."""
    with require_oauth.acquire("role") as token:
        with db.connection(current_app.config["AUTH_DB"]) as conn:
            return jsonify(tuple(
                dictify(role) for role in _user_roles(conn, token.user)))

def validate_password(password, confirm_password) -> str:
    """Validate the provided password."""
    if len(password) < 8:
        raise PasswordError("The password must be at least 8 characters long.")

    if password != confirm_password:
        raise PasswordError("Mismatched password values")

    return password

def validate_username(name: str) -> str:
    """Validate the provides name."""
    if name == "":
        raise UsernameError("User's name not provided.")

    return name

def __assert_not_logged_in__(conn: db.DbConnection):
    bearer = request.headers.get('Authorization')
    if bearer:
        token = token_by_access_token(conn, bearer.split(None)[1]).maybe(# type: ignore[misc]
            False, lambda tok: tok)
        if token:
            raise UserRegistrationError(
                "Cannot register user while authenticated")

@users.route("/register", methods=["POST"])
def register_user() -> Response:
    """Register a user."""
    with db.connection(current_app.config["AUTH_DB"]) as conn:
        __assert_not_logged_in__(conn)

        try:
            form = request.form
            email = validate_email(form.get("email", "").strip(),
                                   check_deliverability=True)
            password = validate_password(
                form.get("password", "").strip(),
                form.get("confirm_password", "").strip())
            user_name = validate_username(form.get("user_name", "").strip())
            with db.cursor(conn) as cursor:
                user, _hashed_password = set_user_password(
                    cursor, save_user(
                        cursor, email["email"], user_name), password)
                assign_default_roles(cursor, user)
                return jsonify(
                    {
                        "user_id": user.user_id,
                        "email": user.email,
                        "name": user.name
                    })
        except sqlite3.IntegrityError as sq3ie:
            current_app.logger.debug(traceback.format_exc())
            raise UserRegistrationError(
                "A user with that email already exists") from sq3ie
        except EmailNotValidError as enve:
            current_app.logger.debug(traceback.format_exc())
            raise(UserRegistrationError(f"Email Error: {str(enve)}")) from enve

    raise Exception(
        "unknown_error", "The system experienced an unexpected error.")

@users.route("/group", methods=["GET"])
@require_oauth("profile group")
def user_group() -> Response:
    """Retrieve the group in which the user is a member."""
    with require_oauth.acquire("profile group") as the_token:
        db_uri = current_app.config["AUTH_DB"]
        with db.connection(db_uri) as conn:
            group = _user_group(conn, the_token.user).maybe(# type: ignore[misc]
                False, lambda grp: grp)# type: ignore[arg-type]

        if group:
            return jsonify(dictify(group))
        raise NotFoundError("User is not a member of any group.")

@users.route("/resources", methods=["GET"])
@require_oauth("profile resource")
def user_resources() -> Response:
    """Retrieve the resources a user has access to."""
    with require_oauth.acquire("profile resource") as the_token:
        db_uri = current_app.config["AUTH_DB"]
        with db.connection(db_uri) as conn:
            return jsonify([
                dictify(resource) for resource in
                _user_resources(conn, the_token.user)])

@users.route("group/join-request", methods=["GET"])
@require_oauth("profile group")
def user_join_request_exists():
    """Check whether a user has an active group join request."""
    def __request_exists__(conn: db.DbConnection, user: User) -> dict[str, Any]:
        with db.cursor(conn) as cursor:
            cursor.execute(
                "SELECT * FROM group_join_requests WHERE requester_id=? AND "
                "status = 'PENDING'",
                (str(user.user_id),))
            res = cursor.fetchone()
            if res:
                return {
                    "request_id": res["request_id"],
                    "exists": True
                }
        return{
            "status": "Not found",
            "exists": False
        }
    with require_oauth.acquire("profile group") as the_token:
        return jsonify(with_db_connection(partial(
            __request_exists__, user=the_token.user)))

@users.route("/list", methods=["GET"])
@require_oauth("profile user")
def list_all_users() -> Response:
    """List all the users."""
    with require_oauth.acquire("profile group") as _the_token:
        return jsonify(tuple(
            dictify(user) for user in with_db_connection(list_users)))
