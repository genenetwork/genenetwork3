"""Functions to check for authorisation."""
from functools import wraps
from typing import Callable, Optional

from flask import g, current_app as app

from gn3.auth import db

from . import privileges as auth_privs
from .errors import AuthorisationError

from ..authentication.users import User

def authorised_p(
        privileges: tuple[str],
        error_message: str = (
            "You lack authorisation to perform requested action"),
        user: Optional[User] = None):
    """Authorisation decorator."""
    assert len(privileges) > 0, "You must provide at least one privilege"
    def __build_authoriser__(func: Callable):
        @wraps(func)
        def __authoriser__(*args, **kwargs):
            the_user = user or (hasattr(g, "user") and g.user)
            if the_user:
                with db.connection(app.config["AUTH_DB"]) as conn:
                    user_privileges = tuple(
                        priv.privilege_id for priv in
                        auth_privs.user_privileges(conn, the_user))

                not_assigned = [
                    priv for priv in privileges if priv not in user_privileges]
                if len(not_assigned) == 0:
                    return func(*args, **kwargs)

            raise AuthorisationError(error_message)
        return __authoriser__
    return __build_authoriser__
