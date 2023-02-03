"""Functions to check for authorisation."""
from functools import wraps
from typing import Callable

from flask import current_app as app

from gn3.auth import db

from . import privileges as auth_privs
from .errors import AuthorisationError

from ..authentication.oauth2.resource_server import require_oauth

def authorised_p(
        privileges: tuple[str],
        error_description: str = (
            "You lack authorisation to perform requested action"),
        oauth2_scope = "profile"):
    """Authorisation decorator."""
    assert len(privileges) > 0, "You must provide at least one privilege"
    def __build_authoriser__(func: Callable):
        @wraps(func)
        def __authoriser__(*args, **kwargs):
            # the_user = user or (hasattr(g, "user") and g.user)
            with require_oauth.acquire(oauth2_scope) as the_token:
                the_user = the_token.user
                if the_user:
                    with db.connection(app.config["AUTH_DB"]) as conn:
                        user_privileges = tuple(
                            priv.privilege_id for priv in
                            auth_privs.user_privileges(conn, the_user))

                    not_assigned = [
                        priv for priv in privileges if priv not in user_privileges]
                    if len(not_assigned) == 0:
                        return func(*args, **kwargs)

                raise AuthorisationError(error_description)
        return __authoriser__
    return __build_authoriser__
