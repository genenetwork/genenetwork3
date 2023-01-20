"""Handle token revocation."""

from flask import current_app
from authlib.oauth2.rfc7009 import RevocationEndpoint as _RevocationEndpoint

from gn3.auth import db
from gn3.auth.authentication.oauth2.models.oauth2token import (
    save_token, OAuth2Token, revoke_token)

from .utilities import query_token as _query_token

class RevocationEndpoint(_RevocationEndpoint):
    """Revoke the tokens"""
    ENDPOINT_NAME = "revoke"
    def query_token(self, token_string: str, token_type_hint: str):
        """Query the token."""
        return _query_token(self, token_string, token_type_hint)

    def revoke_token(self, token: OAuth2Token, request):
        """Revoke token `token`."""
        with db.connection(current_app.config["AUTH_DB"]) as conn:
            save_token(conn, revoke_token(token))
