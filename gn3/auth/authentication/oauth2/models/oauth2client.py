"""OAuth2 Client model."""
import json
import uuid
import datetime
from typing import Sequence, Optional, NamedTuple

from pymonad.maybe import Just, Maybe, Nothing

from gn3.auth import db
from gn3.auth.authentication.users import User, user_by_id

from gn3.auth.authorisation.errors import NotFoundError

class OAuth2Client(NamedTuple):
    """
    Client to the OAuth2 Server.

    This is defined according to the mixin at
    https://docs.authlib.org/en/latest/specs/rfc6749.html#authlib.oauth2.rfc6749.ClientMixin
    """
    client_id: uuid.UUID
    client_secret: str
    client_id_issued_at: datetime.datetime
    client_secret_expires_at: datetime.datetime
    client_metadata: dict
    user: User

    def check_client_secret(self, client_secret: str) -> bool:
        """Check whether the `client_secret` matches this client."""
        return self.client_secret == client_secret

    @property
    def token_endpoint_auth_method(self) -> str:
        """Return the token endpoint authorisation method."""
        return self.client_metadata.get("token_endpoint_auth_method", ["none"])

    @property
    def client_type(self) -> str:
        """
        Return the token endpoint authorisation method.

        Acceptable client types:
        * public: Unable to use registered client secrets, e.g. browsers, apps
          on mobile devices.
        * confidential: able to securely authenticate with authorisation server
          e.g. being able to keep their registered client secret safe.
        """
        return self.client_metadata.get("client_type", "public")

    def check_endpoint_auth_method(self, method: str, endpoint: str) -> bool:
        """
        Check if the client supports the given method for the given endpoint.

        Acceptable methods:
        * none: Client is a public client and does not have a client secret
        * client_secret_post: Client uses the HTTP POST parameters
        * client_secret_basic: Client uses HTTP Basic
        """
        if endpoint == "token":
            return (method in self.token_endpoint_auth_method
                    and method == "client_secret_post")
        if endpoint in ("introspection", "revoke"):
            return (method in self.token_endpoint_auth_method
                    and method == "client_secret_basic")
        return False

    @property
    def id(self):# pylint: disable=[invalid-name]
        """Return the client_id."""
        return self.client_id

    @property
    def grant_types(self) -> Sequence[str]:
        """
        Return the grant types that this client supports.

        Valid grant types:
        * authorisation_code
        * implicit
        * client_credentials
        * password
        """
        return self.client_metadata.get("grant_types", [])

    def check_grant_type(self, grant_type: str) -> bool:
        """
        Validate that client can handle the given grant types
        """
        return grant_type in self.grant_types

    @property
    def redirect_uris(self) -> Sequence[str]:
        """Return the redirect_uris that this client supports."""
        return self.client_metadata.get('redirect_uris', [])

    def check_redirect_uri(self, redirect_uri: str) -> bool:
        """
        Check whether the given `redirect_uri` is one of the expected ones.
        """
        return redirect_uri in self.redirect_uris

    @property
    def response_types(self) -> Sequence[str]:
        """Return the response_types that this client supports."""
        return self.client_metadata.get("response_type", [])

    def check_response_type(self, response_type: str) -> bool:
        """Check whether this client supports `response_type`."""
        return response_type in self.response_types

    @property
    def scope(self) -> Sequence[str]:
        """Return valid scopes for this client."""
        return tuple(set(self.client_metadata.get("scope", [])))

    def get_allowed_scope(self, scope: str) -> str:
        """Return list of scopes in `scope` that are supported by this client."""
        if not bool(scope):
            return ""
        requested = scope.split()
        return " ".join(sorted(set(
            scp for scp in requested if scp in self.scope)))

    def get_client_id(self):
        """Return this client's identifier."""
        return self.client_id

    def get_default_redirect_uri(self) -> str:
        """Return the default redirect uri"""
        return self.client_metadata.get("default_redirect_uri", "")

def client(conn: db.DbConnection, client_id: uuid.UUID,
           user: Optional[User] = None) -> Maybe:
    """Retrieve a client by its ID"""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "SELECT * FROM oauth2_clients WHERE client_id=?", (str(client_id),))
        result = cursor.fetchone()
        the_user = user
        if result:
            if not bool(the_user):
                try:
                    the_user = user_by_id(conn, result["user_id"])
                except NotFoundError as _nfe:
                    the_user = None

            return Just(
                OAuth2Client(uuid.UUID(result["client_id"]),
                             result["client_secret"],
                             datetime.datetime.fromtimestamp(
                                 result["client_id_issued_at"]),
                             datetime.datetime.fromtimestamp(
                                 result["client_secret_expires_at"]),
                             json.loads(result["client_metadata"]),
                             the_user))# type: ignore[arg-type]

    return Nothing

def client_by_id_and_secret(conn: db.DbConnection, client_id: uuid.UUID,
                            client_secret: str) -> OAuth2Client:
    """Retrieve a client by its ID and secret"""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "SELECT * FROM oauth2_clients WHERE client_id=? AND "
            "client_secret=?",
            (str(client_id), client_secret))
        row = cursor.fetchone()
        if bool(row):
            return OAuth2Client(
                client_id, client_secret,
                datetime.datetime.fromtimestamp(row["client_id_issued_at"]),
                datetime.datetime.fromtimestamp(row["client_secret_expires_at"]),
                json.loads(row["client_metadata"]),
                user_by_id(conn, uuid.UUID(row["user_id"])))

        raise NotFoundError(f"Could not find client with ID '{client_id}'")
