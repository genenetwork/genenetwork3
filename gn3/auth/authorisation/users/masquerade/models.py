"""Functions for handling masquerade."""
from uuid import uuid4
from functools import wraps
from datetime import datetime

from flask import current_app as app

from gn3.auth import db

from gn3.auth.authorisation.errors import ForbiddenAccess
from gn3.auth.authorisation.roles.models import user_roles

from gn3.auth.authentication.users import User
from gn3.auth.authentication.oauth2.models.oauth2token import (
    OAuth2Token, save_token)

__FIVE_HOURS__ = (60 * 60 * 5)

def can_masquerade(func):
    """Security decorator."""
    @wraps(func)
    def __checker__(*args, **kwargs):
        if len(args) == 3:
            conn, token, _masq_user = args
        elif len(args) == 2:
            conn, token = args
        elif len(args) == 1:
            conn = args[0]
            token = kwargs["original_token"]
        else:
            conn = kwargs["conn"]
            token = kwargs["original_token"]

        masq_privs = [priv for role in user_roles(conn, token.user)
                      for priv in role.privileges
                      if priv.privilege_id == "system:user:masquerade"]
        if len(masq_privs) == 0:
            raise ForbiddenAccess(
                "You do not have the ability to masquerade as another user.")
        return func(*args, **kwargs)
    return __checker__

@can_masquerade
def masquerade_as(
        conn: db.DbConnection,
        original_token: OAuth2Token,
        masqueradee: User) -> OAuth2Token:
    """Get a token that enables `masquerader` to act as `masqueradee`."""
    token_details = app.config["OAUTH2_SERVER"].generate_token(
        client=original_token.client,
        grant_type="authorization_code",
        user=masqueradee,
        expires_in=__FIVE_HOURS__,
        include_refresh_token=True)
    new_token = OAuth2Token(
        token_id=uuid4(),
        client=original_token.client,
        token_type=token_details["token_type"],
        access_token=token_details["access_token"],
        refresh_token=token_details.get("refresh_token"),
        scope=original_token.scope,
        revoked=False,
        issued_at=datetime.now(),
        expires_in=token_details["expires_in"],
        user=masqueradee)
    save_token(conn, new_token)
    return new_token
