"""OAuth2 Token"""
import uuid
import datetime
from typing import NamedTuple, Optional

from pymonad.maybe import Just, Maybe, Nothing

from gn3.auth import db
from gn3.auth.authentication.users import User, user_by_id

from gn3.auth.authorisation.errors import NotFoundError

from .oauth2client import client, OAuth2Client

class OAuth2Token(NamedTuple):
    """Implement Tokens for OAuth2."""
    token_id: uuid.UUID
    client: OAuth2Client
    token_type: str
    access_token: str
    refresh_token: Optional[str]
    scope: str
    revoked: bool
    issued_at: datetime.datetime
    expires_in: int
    user: User

    @property
    def expires_at(self) -> datetime.datetime:
        """Return the time when the token expires."""
        return self.issued_at + datetime.timedelta(seconds=self.expires_in)

    def check_client(self, client: OAuth2Client) -> bool:# pylint: disable=[redefined-outer-name]
        """Check whether the token is issued to given `client`."""
        return client.client_id == self.client.client_id

    def get_expires_in(self) -> int:
        """Return the `expires_in` value for the token."""
        return self.expires_in

    def get_scope(self) -> str:
        """Return the valid scope for the token."""
        return self.scope

    def is_expired(self) -> bool:
        """Check whether the token is expired."""
        return self.expires_at < datetime.datetime.now()

    def is_revoked(self):
        """Check whether the token has been revoked."""
        return self.revoked

def __token_from_resultset__(conn: db.DbConnection, rset) -> Maybe:
    __identity__ = lambda val: val
    try:
        the_user = user_by_id(conn, uuid.UUID(rset["user_id"]))
    except NotFoundError as _nfe:
        the_user = None
    the_client = client(conn, uuid.UUID(rset["client_id"]), the_user)

    if the_client.is_just() and bool(the_user):
        return Just(OAuth2Token(token_id=uuid.UUID(rset["token_id"]),
                                client=the_client.maybe(None, __identity__),
                                token_type=rset["token_type"],
                                access_token=rset["access_token"],
                                refresh_token=rset["refresh_token"],
                                scope=rset["scope"],
                                revoked=(rset["revoked"] == 1),
                                issued_at=datetime.datetime.fromtimestamp(
                                    rset["issued_at"]),
                                expires_in=rset["expires_in"],
                                user=the_user))# type: ignore[arg-type]

    return Nothing

def token_by_access_token(conn: db.DbConnection, token_str: str) -> Maybe:
    """Retrieve token by its token string"""
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM oauth2_tokens WHERE access_token=?",
                       (token_str,))
        res = cursor.fetchone()
        if res:
            return __token_from_resultset__(conn, res)

    return Nothing

def token_by_refresh_token(conn: db.DbConnection, token_str: str) -> Maybe:
    """Retrieve token by its token string"""
    with db.cursor(conn) as cursor:
        cursor.execute(
            "SELECT * FROM oauth2_tokens WHERE refresh_token=?",
            (token_str,))
        res = cursor.fetchone()
        if res:
            return __token_from_resultset__(conn, res)

    return Nothing

def revoke_token(token: OAuth2Token) -> OAuth2Token:
    """
    Return a new token derived from `token` with the `revoked` field set to
    `True`.
    """
    return OAuth2Token(
        token_id=token.token_id, client=token.client,
        token_type=token.token_type, access_token=token.access_token,
        refresh_token=token.refresh_token, scope=token.scope, revoked=True,
        issued_at=token.issued_at, expires_in=token.expires_in, user=token.user)

def save_token(conn: db.DbConnection, token: OAuth2Token) -> None:
    """Save/Update the token."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            ("INSERT INTO oauth2_tokens VALUES (:token_id, :client_id, "
             ":token_type, :access_token, :refresh_token, :scope, :revoked, "
             ":issued_at, :expires_in, :user_id) "
             "ON CONFLICT (token_id) DO UPDATE SET "
             "refresh_token=:refresh_token, revoked=:revoked, "
             "expires_in=:expires_in "
             "WHERE token_id=:token_id"),
            {
                "token_id": str(token.token_id),
                "client_id": str(token.client.client_id),
                "token_type": token.token_type,
                "access_token": token.access_token,
                "refresh_token": token.refresh_token,
                "scope": token.scope,
                "revoked": 1 if token.revoked else 0,
                "issued_at": int(token.issued_at.timestamp()),
                "expires_in": token.expires_in,
                "user_id": str(token.user.user_id)
            })
