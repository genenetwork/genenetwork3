"""UI utilities for the auth system."""
from functools import wraps
from datetime import datetime, timezone
from flask import flash, session, request, url_for, redirect

from gn3.auth.authentication.users import User
from gn3.auth.db_utils import with_db_connection
from gn3.auth.authorisation.roles.models import user_roles

SESSION_KEY = "session_details"

def __session_expired__():
    """Check whether the session has expired."""
    return datetime.now(tz=timezone.utc) >= session[SESSION_KEY]["expires"]

def logged_in(func):
    """Verify the user is logged in."""
    @wraps(func)
    def __logged_in__(*args, **kwargs):
        if bool(session.get(SESSION_KEY)) and not __session_expired__():
            return func(*args, **kwargs)
        flash("You need to be logged in to access that page.", "alert-danger")
        return redirect(url_for(
            "oauth2.admin.login", next=request.url_rule.endpoint))
    return __logged_in__

def is_admin(func):
    """Verify user is a system admin."""
    @wraps(func)
    @logged_in
    def __admin__(*args, **kwargs):
        admin_roles = [
            role for role in with_db_connection(
                lambda conn: user_roles(
                    conn, User(**session[SESSION_KEY]["user"])))
            if role.role_name == "system-administrator"]
        if len(admin_roles) > 0:
            return func(*args, **kwargs)
        flash("Expected a system administrator.", "alert-danger")
        flash("You have been logged out of the system.", "alert-info")
        session.pop(SESSION_KEY)
        return redirect(url_for("oauth2.admin.login"))
    return __admin__
