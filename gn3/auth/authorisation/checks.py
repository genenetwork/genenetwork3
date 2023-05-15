"""Functions to check for authorisation."""
from functools import wraps
from typing import Callable

from flask import request, current_app as app

from gn3.auth import db

from . import privileges as auth_privs
from .errors import InvalidData, AuthorisationError

from ..authentication.oauth2.resource_server import require_oauth

def __system_privileges_in_roles__(conn, user):
    """
    This really is a hack since groups are not treated as resources at the
    moment of writing this.

    We need a way of allowing the user to have the system:group:* privileges.
    """
    query = (
        "SELECT DISTINCT p.* FROM users AS u "
        "INNER JOIN group_user_roles_on_resources AS guror "
        "ON u.user_id=guror.user_id "
        "INNER JOIN roles AS r ON guror.role_id=r.role_id "
        "INNER JOIN role_privileges AS rp ON r.role_id=rp.role_id "
        "INNER JOIN privileges AS p ON rp.privilege_id=p.privilege_id "
        "WHERE u.user_id=? AND p.privilege_id LIKE 'system:%'")
    with db.cursor(conn) as cursor:
        cursor.execute(query, (str(user.user_id),))
        return (row["privilege_id"] for row in cursor.fetchall())

def authorised_p(
        privileges: tuple[str, ...],
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
                            auth_privs.user_privileges(conn, the_user)) + tuple(
                                priv_id for priv_id in
                                __system_privileges_in_roles__(conn, the_user))

                    not_assigned = [
                        priv for priv in privileges if priv not in user_privileges]
                    if len(not_assigned) == 0:
                        return func(*args, **kwargs)

                raise AuthorisationError(error_description)
        return __authoriser__
    return __build_authoriser__

def require_json(func):
    """Ensure the request has JSON data."""
    @wraps(func)
    def __req_json__(*args, **kwargs):
        if bool(request.json):
            return func(*args, **kwargs)
        raise InvalidData("Expected JSON data in the request.")
    return __req_json__
