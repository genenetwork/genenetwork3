"""UI utilities for the auth system."""
from functools import wraps
from flask import flash, url_for, redirect

from gn3.auth.authentication.users import User
from gn3.auth.db_utils import with_db_connection
from gn3.auth.authorisation.roles.models import user_roles

from gn3.session import logged_in, session_user, clear_session_info

def is_admin(func):
    """Verify user is a system admin."""
    @wraps(func)
    @logged_in
    def __admin__(*args, **kwargs):
        admin_roles = [
            role for role in with_db_connection(
                lambda conn: user_roles(
                    conn, User(**session_user())))
            if role.role_name == "system-administrator"]
        if len(admin_roles) > 0:
            return func(*args, **kwargs)
        flash("Expected a system administrator.", "alert-danger")
        flash("You have been logged out of the system.", "alert-info")
        clear_session_info()
        return redirect(url_for("oauth2.admin.login"))
    return __admin__
