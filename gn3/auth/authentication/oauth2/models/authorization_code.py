"""Model and functions for handling the Authorisation Code"""
from uuid import UUID
from datetime import datetime
from typing import NamedTuple

from pymonad.maybe import Just, Maybe, Nothing

from gn3.auth import db

from .oauth2client import OAuth2Client

from ...users import User, user_by_id

__5_MINUTES__ = 300 # in seconds

class AuthorisationCode(NamedTuple):
    """
    The AuthorisationCode model for the auth(entic|oris)ation system.
    """
    # Instance variables
    code_id: UUID
    code: str
    client: OAuth2Client
    redirect_uri: str
    scope: str
    nonce: str
    auth_time: int
    code_challenge: str
    code_challenge_method: str
    user: User

    @property
    def response_type(self) -> str:
        """
        For authorisation code flow, the response_type type MUST always be
        'code'.
        """
        return "code"

    def is_expired(self):
        """Check whether the code is expired."""
        return self.auth_time + __5_MINUTES__ < datetime.now().timestamp()

    def get_redirect_uri(self):
        """Get the redirect URI"""
        return self.redirect_uri

    def get_scope(self):
        """Return the assigned scope for this AuthorisationCode."""
        return self.scope

    def get_nonce(self):
        """Get the one-time use token."""
        return self.nonce

def authorisation_code(conn: db.DbConnection ,
                       code: str,
                       client: OAuth2Client) -> Maybe[AuthorisationCode]:
    """
    Retrieve the authorisation code object that corresponds to `code` and the
    given OAuth2 client.
    """
    with db.cursor(conn) as cursor:
        query = ("SELECT * FROM authorisation_code "
                 "WHERE code=:code AND client_id=:client_id")
        cursor.execute(
            query, {"code": code, "client_id": str(client.client_id)})
        result = cursor.fetchone()
        if result:
            return Just(AuthorisationCode(
                UUID(result["code_id"]), result["code"], client,
                result["redirect_uri"], result["scope"], result["nonce"],
                int(result["auth_time"]), result["code_challenge"],
                result["code_challenge_method"],
                user_by_id(conn, UUID(result["user_id"]))))
        return Nothing

def save_authorisation_code(conn: db.DbConnection,
                            auth_code: AuthorisationCode) -> AuthorisationCode:
    """Persist the `auth_code` into the database."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "INSERT INTO authorisation_code VALUES("
            ":code_id, :code, :client_id, :redirect_uri, :scope, :nonce, "
            ":auth_time, :code_challenge, :code_challenge_method, :user_id"
            ")",
            {
                **auth_code._asdict(),
                "code_id": str(auth_code.code_id),
                "client_id": str(auth_code.client.client_id),
                "user_id": str(auth_code.user.user_id)
            })
        return auth_code
