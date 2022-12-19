"""Handle introspection of tokens."""
import datetime
from urllib.parse import urlparse

from flask import request as flask_request
from authlib.oauth2.rfc7662 import (
    IntrospectionEndpoint as _IntrospectionEndpoint)

from gn3.auth.authentication.oauth2.models.oauth2token import OAuth2Token

from .utilities import query_token as _query_token

def get_token_user_sub(token: OAuth2Token) -> str:# pylint: disable=[unused-argument]
    """
    Return the token's subject as defined in
    https://datatracker.ietf.org/doc/html/rfc7519#section-4.1.2
    """
    ## For now a dummy return to prevent issues.
    return "sub"

class IntrospectionEndpoint(_IntrospectionEndpoint):
    """Introspect token."""
    def query_token(self, token_string: str, token_type_hint: str):
        """Query the token."""
        return _query_token(self, token_string, token_type_hint)

    def introspect_token(self, token: OAuth2Token) -> dict:# pylint: disable=[no-self-use]
        """Return the introspection information."""
        url = urlparse(flask_request.url)
        return {
            "active": True,
            "scope": token.get_scope(),
            "client_id": token.client.client_id,
            "username": token.user.name,
            "token_type": token.token_type,
            "exp": int(token.expires_at.timestamp()),
            "iat": int(token.issued_at.timestamp()),
            "nbf": int(
                (token.issued_at - datetime.timedelta(seconds=120)).timestamp()),
            # "sub": get_token_user_sub(token),
            "aud": token.client.client_id,
            "iss": f"{url.scheme}://{url.netloc}",
            "jti": token.token_id
        }

    def check_permission(self, token, client, request):# pylint: disable=[unused-argument, no-self-use]
        """Check that the client has permission to introspect token."""
        return client.client_type == "internal"
