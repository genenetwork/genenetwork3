"""Classes and function for Authorisation Code flow."""
import uuid
import string
import random
from typing import Optional
from datetime import datetime

from flask import current_app as app
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc7636 import create_s256_code_challenge

from gn3.auth import db
from gn3.auth.db_utils import with_db_connection
from gn3.auth.authentication.users import User

from ..models.oauth2client import OAuth2Client
from ..models.authorization_code import (
    AuthorisationCode, authorisation_code, save_authorisation_code)

class AuthorisationCodeGrant(grants.AuthorizationCodeGrant):
    """Implement the 'Authorisation Code' grant."""
    TOKEN_ENDPOINT_AUTH_METHODS: list[str] = [
        "client_secret_basic", "client_secret_post"]
    AUTHORIZATION_CODE_LENGTH: int = 48
    TOKEN_ENDPOINT_HTTP_METHODS = ['POST']
    GRANT_TYPE = "authorization_code"
    RESPONSE_TYPES = {'code'}

    def save_authorization_code(self, code, request):
        """Persist the authorisation code to database."""
        client = request.client
        nonce = "".join(random.sample(string.ascii_letters + string.digits,
                                      k=self.AUTHORIZATION_CODE_LENGTH))
        return __save_authorization_code__(AuthorisationCode(
            uuid.uuid4(), code, client, request.redirect_uri, request.scope,
            nonce, int(datetime.now().timestamp()),
            create_s256_code_challenge(app.config["SECRET_KEY"]),
            "S256", request.user))

    def query_authorization_code(self, code, client):
        """Retrieve the code from the database."""
        return __query_authorization_code__(code, client)

    def delete_authorization_code(self, authorization_code):# pylint: disable=[no-self-use]
        """Delete the authorisation code."""
        with db.connection(app.config["AUTH_DB"]) as conn:
            with db.cursor(conn) as cursor:
                cursor.execute(
                    "DELETE FROM authorisation_code WHERE code_id=?",
                    (str(authorization_code.code_id),))

    def authenticate_user(self, authorization_code) -> Optional[User]:
        """Authenticate the user who own the authorisation code."""
        query = (
            "SELECT users.* FROM authorisation_code LEFT JOIN users "
            "ON authorisation_code.user_id=users.user_id "
            "WHERE authorisation_code.code=?")
        with db.connection(app.config["AUTH_DB"]) as conn:
            with db.cursor(conn) as cursor:
                cursor.execute(query, (str(authorization_code.code),))
                res = cursor.fetchone()
                if res:
                    return User(
                        uuid.UUID(res["user_id"]), res["email"], res["name"])

        return None

def __query_authorization_code__(
        code: str, client: OAuth2Client) -> AuthorisationCode:
    """A helper function that creates a new database connection.

    This is found to be necessary since the `AuthorizationCodeGrant` class(es)
    do not have a way to pass the database connection."""
    def __auth_code__(conn) -> str:
        the_code = authorisation_code(conn, code, client)
        return the_code.maybe(None, lambda cde: cde) # type: ignore[misc, arg-type, return-value]

    return with_db_connection(__auth_code__)

def __save_authorization_code__(code: AuthorisationCode) -> AuthorisationCode:
    """A helper function that creates a new database connection.

    This is found to be necessary since the `AuthorizationCodeGrant` class(es)
    do not have a way to pass the database connection."""
    return with_db_connection(lambda conn: save_authorisation_code(conn, code))
