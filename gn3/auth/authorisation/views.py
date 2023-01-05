"""Endpoints for the authorisation stuff."""
from typing import Tuple, Optional
from flask import request, jsonify, current_app

from gn3.auth import db
from gn3.auth.blueprint import oauth2

from .groups import user_group
from .errors import UserRegistrationError
from .roles import user_roles as _user_roles

from ..authentication.oauth2.resource_server import require_oauth
from ..authentication.users import User, save_user, set_user_password
from ..authentication.oauth2.models.oauth2token import token_by_access_token

@oauth2.route("/user", methods=["GET"])
@require_oauth("profile")
def user_details():
    """Return user's details."""
    with require_oauth.acquire("profile") as the_token:
        user = the_token.user
        with db.connection(current_app.config["AUTH_DB"]) as conn, db.cursor(conn) as cursor:
            group = user_group(cursor, user)

        return jsonify({
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
            "group": group.maybe(False, lambda grp: grp)
        })

@oauth2.route("/user-roles", methods=["GET"])
@require_oauth
def user_roles():
    """Return the non-resource roles assigned to the user."""
    with require_oauth.acquire("role") as token:
        with db.connection(current_app.config["AUTH_DB"]) as conn:
            return jsonify(_user_roles(conn, token.user))

def __email_valid__(email: str) -> Tuple[bool, Optional[str]]:
    """Validate the email address."""
    if email == "":
        return False, "Empty email address"

    ## Check that the address is a valid email address
    ## Review use of `email-validator` or `pyIsEmail` python packages for
    ## validating the emails, if it turns out this is important.

    ## Success
    return True, None

def __password_valid__(password, confirm_password) -> Tuple[bool, Optional[str]]:
    if password == "" or confirm_password == "":
        return False, "Empty password value"

    if password != confirm_password:
        return False, "Mismatched password values"

    return True, None

def __user_name_valid__(name: str) -> Tuple[bool, Optional[str]]:
    if name == "":
        return False, "User's name not provided."

    return True, None

def __assert_not_logged_in__(conn: db.DbConnection):
    bearer = request.headers.get('Authorization')
    if bearer:
        token = token_by_access_token(conn, bearer.split(None)[1]).maybe(# type: ignore[misc]
            False, lambda tok: tok)
        if token:
            raise UserRegistrationError(
                "Cannot register user while authenticated")

@oauth2.route("/register-user", methods=["POST"])
def register_user():
    """Register a user."""
    with db.connection(current_app.config["AUTH_DB"]) as conn:
        __assert_not_logged_in__(conn)

        form = request.form
        email = form.get("email", "")
        password = form.get("password", "")
        user_name = form.get("user_name", "")
        errors = tuple(
                error[1] for error in
            [__email_valid__(email),
             __password_valid__(password, form.get("confirm_password", "")),
             __user_name_valid__(user_name)]
            if error[0])
        if len(errors) > 0:
            raise UserRegistrationError(*errors)

        with db.cursor(conn) as cursor:
            user, _hashed_password = set_user_password(
                cursor, save_user(cursor, email, user_name), password)
            return jsonify(
                {
                    "user_id": user.user_id,
                    "email": user.email,
                    "name": user.name
                }), 200

    raise Exception(
        "unknown_error", "The system experienced an unexpected error.")
