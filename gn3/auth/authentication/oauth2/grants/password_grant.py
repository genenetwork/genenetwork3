"""Allows users to authenticate directly."""

from flask import current_app as app
from authlib.oauth2.rfc6749 import grants

from gn3.auth import db
from gn3.auth.authentication.users import valid_login, user_by_email

from gn3.auth.authorisation.errors import NotFoundError

class PasswordGrant(grants.ResourceOwnerPasswordCredentialsGrant):
    """Implement the 'Password' grant."""
    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "client_secret_post"]

    def authenticate_user(self, username, password):
        "Authenticate the user with their username and password."
        with db.connection(app.config["AUTH_DB"]) as conn:
            try:
                user = user_by_email(conn, username)
                return user if valid_login(conn, user, password) else None
            except NotFoundError as _nfe:
                return None
