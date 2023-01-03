"""Protect the resources endpoints"""

from flask import current_app as app
from authlib.oauth2.rfc6750 import BearerTokenValidator as _BearerTokenValidator
from authlib.integrations.flask_oauth2 import ResourceProtector

from gn3.auth import db
from gn3.auth.authentication.oauth2.models.oauth2token import token_by_access_token

class BearerTokenValidator(_BearerTokenValidator):
    """Extends `authlib.oauth2.rfc6750.BearerTokenValidator`"""
    def authenticate_token(self, token_string: str):
        with db.connection(app.config["AUTH_DB"]) as conn:
            return token_by_access_token(conn, token_string).maybe(# type: ignore[misc]
                None, lambda tok: tok)

require_oauth = ResourceProtector()

require_oauth.register_token_validator(BearerTokenValidator())
