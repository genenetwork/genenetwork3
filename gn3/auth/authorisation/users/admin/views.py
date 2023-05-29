"""UI for admin stuff"""
from datetime import datetime, timezone, timedelta

from email_validator import validate_email, EmailNotValidError
from flask import (
    flash,
    session,
    request,
    url_for,
    redirect,
    Blueprint,
    current_app,
    render_template)

from gn3.auth import db
from gn3.auth.authentication.users import valid_login, user_by_email

from .ui import SESSION_KEY, is_admin

admin = Blueprint("admin", __name__)

@admin.before_request
def update_expires():
    """Update session expiration."""
    if bool(session.get(SESSION_KEY)):
        now = datetime.now(tz=timezone.utc)
        if now >= session[SESSION_KEY]["expires"]:
            flash("Session has expired. Logging out...", "alert-warning")
            session.pop(SESSION_KEY)
            return redirect("/version")
        # If not expired, extend expiry.
        session[SESSION_KEY]["expires"] = now + timedelta(minutes=10)

    return None

@admin.route("/login", methods=["GET", "POST"])
def login():
    """Log in to GN3 directly without OAuth2 client."""
    if request.method == "GET":
        return render_template(
            "login.html", next_uri=request.args.get("next", "/api/version"))

    form = request.form
    next_uri = form.get("next_uri", "/api/version")
    error_message = "Invalid email or password provided."
    login_page = redirect(url_for("oauth2.admin.login", next=next_uri))
    try:
        email = validate_email(form.get("email", "").strip(),
                               check_deliverability=False)
        password = form.get("password")
        with db.connection(current_app.config["AUTH_DB"]) as conn:
            user = user_by_email(conn, email["email"])
            if valid_login(conn, user, password):
                session[SESSION_KEY] = {
                    "user": user._asdict(),
                    "expires": datetime.now(tz=timezone.utc) + timedelta(minutes=10)
                }
                return redirect(next_uri)
            flash(error_message, "alert-danger")
            return login_page
    except EmailNotValidError as _enve:
        flash(error_message, "alert-danger")
        return login_page

@admin.route("/logout", methods=["GET"])
def logout():
    """Log out the admin."""
    if not bool(session.get(SESSION_KEY)):
        flash("Not logged in.", "alert-info")
        return redirect(url_for("general.version"))
    session.pop(SESSION_KEY)
    flash("Logged out", "alert-success")
    return redirect(url_for("general.version"))

@admin.route("/register-client", methods=["GET", "POST"])
@is_admin
def register_client():
    """Register an OAuth2 client."""
    return "WOULD REGISTER ..."
