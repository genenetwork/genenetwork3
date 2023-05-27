"""Initialise the OAuth2 Server"""
import uuid
import datetime
from typing import Callable

from flask import Flask, current_app
from authlib.oauth2.rfc6749.errors import InvalidClientError
from authlib.integrations.flask_oauth2 import AuthorizationServer
# from authlib.oauth2.rfc7636 import CodeChallenge

from gn3.auth import db

from .models.oauth2client import client
from .models.oauth2token import OAuth2Token, save_token

from .grants.password_grant import PasswordGrant
from .grants.authorisation_code_grant import AuthorisationCodeGrant

from .endpoints.revocation import RevocationEndpoint
from .endpoints.introspection import IntrospectionEndpoint

def create_query_client_func() -> Callable:
    """Create the function that loads the client."""
    def __query_client__(client_id: uuid.UUID):
        # use current_app rather than passing the db_uri to avoid issues
        # when config changes, e.g. while testing.
        with db.connection(current_app.config["AUTH_DB"]) as conn:
            the_client = client(conn, client_id).maybe(
                None, lambda clt: clt) # type: ignore[misc]
            if bool(the_client):
                return the_client
            raise InvalidClientError(
                "No client found for the given CLIENT_ID and CLIENT_SECRET.")

    return __query_client__

def create_save_token_func(token_model: type) -> Callable:
    """Create the function that saves the token."""
    def __save_token__(token, request):
        with db.connection(current_app.config["AUTH_DB"]) as conn:
            save_token(
                conn, token_model(
                    token_id=uuid.uuid4(), client=request.client,
                    user=request.user,
                    **{
                        "refresh_token": None, "revoked": False,
                        "issued_at": datetime.datetime.now(),
                        **token
                    }))

    return __save_token__

def setup_oauth2_server(app: Flask) -> None:
    """Set's up the oauth2 server for the flask application."""
    server = AuthorizationServer()
    server.register_grant(PasswordGrant)

    # Figure out a common `code_verifier` for GN2 and GN3 and set
    # server.register_grant(AuthorisationCodeGrant, [CodeChallenge(required=False)])
    # below
    server.register_grant(AuthorisationCodeGrant)

    # register endpoints
    server.register_endpoint(RevocationEndpoint)
    server.register_endpoint(IntrospectionEndpoint)

    # init server
    server.init_app(
        app,
        query_client=create_query_client_func(),
        save_token=create_save_token_func(OAuth2Token))
    app.config["OAUTH2_SERVER"] = server
