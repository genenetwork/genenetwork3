"""endpoint utilities"""
from typing import Any, Optional

from flask import current_app
from pymonad.maybe import Nothing

from gn3.auth import db
from gn3.auth.authentication.oauth2.models.oauth2token import (
    OAuth2Token, token_by_access_token, token_by_refresh_token)

def query_token(# pylint: disable=[unused-argument]
        endpoint_object: Any, token_str: str, token_type_hint) -> Optional[
            OAuth2Token]:
    """Retrieve the token from the database."""
    __identity__ = lambda val: val
    token = Nothing
    with db.connection(current_app.config["AUTH_DB"]) as conn:
        if token_type_hint == "access_token":
            token = token_by_access_token(conn, token_str)
        if token_type_hint == "access_token":
            token = token_by_refresh_token(conn, token_str)

        return token.maybe(
            token_by_access_token(conn, token_str).maybe(
                token_by_refresh_token(conn, token_str).maybe(
                    None, __identity__),
                __identity__),
            __identity__)

    return None
