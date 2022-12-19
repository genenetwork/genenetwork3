"""Classes and function for Authorisation Code flow."""
import uuid
from typing import Optional

from flask import current_app as app
from authlib.oauth2.rfc6749 import grants

from gn3.auth import db
from gn3.auth.authentication.users import User

class AuthorisationCodeGrant(grants.AuthorizationCodeGrant):
    """Implement the 'Authorisation Code' grant."""
    TOKEN_ENDPOINT_AUTH_METHODS = ["client_secret_basic", "client_secret_post"]

    def save_authorization_code(self, code, request):
        """Persist the authorisation code to database."""
        raise Exception("NOT IMPLEMENTED!", self, code, request)

    def query_authorization_code(self, code, client):
        """Retrieve the code from the database."""
        raise Exception("NOT IMPLEMENTED!", self, code, client)

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
                cursor.execute(query, (str(authorization_code.user_id),))
                res = cursor.fetchone()
                if res:
                    return User(
                        uuid.UUID(res["user_id"]), res["email"], res["name"])

        return None
