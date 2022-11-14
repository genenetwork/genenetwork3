"""The authorisation module."""
from functools import wraps
from typing import Union, Callable

from flask import g, current_app as app

from gn3.auth import db
from . import privileges as auth_privs

def authorised_p(
        privileges: tuple[str] = tuple(),
        success_message: Union[str, bool] = False,
        error_message: Union[str, bool] = False):
    """Authorisation decorator."""
    assert len(privileges) > 0, "You must provide at least one privilege"
    def __build_authoriser__(func: Callable):
        @wraps(func)
        def __authoriser__(*args, **kwargs):
            if hasattr(g, "user_id") and g.user_id:
                with db.connection(app.config["AUTH_DB"]) as conn:
                    user_privileges = auth_privs.user_privileges(conn, g.user_id)

                not_assigned = [
                    priv for priv in privileges if priv not in user_privileges]
                if len(not_assigned) == 0:
                    return {
                        "status": "success",
                        "message": success_message or "successfully authorised",
                        "results": func(*args, **kwargs)}
            return {
                "status": "error",
                "message": f"Unauthorised: {error_message or ''}"
            }
        return __authoriser__
    return __build_authoriser__
