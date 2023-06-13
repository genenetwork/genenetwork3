"""Handle any GN3 sessions."""
from functools import wraps
from datetime import datetime, timezone, timedelta

from flask import flash, request, session, url_for, redirect

__SESSION_KEY__ = "GN::3::session_details"

def __session_expired__():
    """Check whether the session has expired."""
    return datetime.now(tz=timezone.utc) >= session[__SESSION_KEY__]["expires"]

def logged_in(func):
    """Verify the user is logged in."""
    @wraps(func)
    def __logged_in__(*args, **kwargs):
        if bool(session.get(__SESSION_KEY__)) and not __session_expired__():
            return func(*args, **kwargs)
        flash("You need to be logged in to access that page.", "alert-danger")
        return redirect(url_for(
            "oauth2.admin.login", next=request.url_rule.endpoint))
    return __logged_in__

def session_info():
    """Retrieve the session information."""
    return session.get(__SESSION_KEY__, False)

def session_user():
    """Retrieve session user."""
    info = session_info()
    return info and info["user"]

def clear_session_info():
    """Clear any session info."""
    try:
        session.pop(__SESSION_KEY__)
    except KeyError as _keyerr:
        pass

def session_expired() -> bool:
    """
    Check whether the session has expired. Will always return `True` if no
    session currently exists.
    """
    if bool(session.get(__SESSION_KEY__)):
        now = datetime.now(tz=timezone.utc)
        return now >= session[__SESSION_KEY__]["expires"]
    return True

def update_expiry() -> bool:
    """Update the session expiry and return a boolean indicating success."""
    if not session_expired():
        now = datetime.now(tz=timezone.utc)
        session[__SESSION_KEY__]["expires"] = now + timedelta(minutes=10)
        return True
    return False

def update_session_info(**info):
    """Update the session information."""
    session[__SESSION_KEY__] = info
