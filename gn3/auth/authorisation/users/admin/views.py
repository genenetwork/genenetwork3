"""UI for admin stuff"""
import uuid
import random
import string
from functools import partial
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
from gn3.auth.db_utils import with_db_connection

from gn3.auth.authentication.oauth2.models.oauth2client import (
    save_client,
    OAuth2Client)
from gn3.auth.authentication.users import (
    User,
    user_by_id,
    valid_login,
    user_by_email,
    hash_password)

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
            return redirect(url_for("oauth2.admin.login"))
        # If not expired, extend expiry.
        session[SESSION_KEY]["expires"] = now + timedelta(minutes=10)

    return None

@admin.route("/dashboard", methods=["GET"])
def dashboard():
    """Admin dashboard."""
    return render_template("admin/dashboard.html")

@admin.route("/login", methods=["GET", "POST"])
def login():
    """Log in to GN3 directly without OAuth2 client."""
    if request.method == "GET":
        return render_template(
            "admin/login.html",
            next_uri=request.args.get("next", "oauth2.admin.dashboard"))

    form = request.form
    next_uri = form.get("next_uri", "oauth2.admin.dashboard")
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
                return redirect(url_for(next_uri))
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
        return redirect(url_for("oauth2.admin.login"))
    session.pop(SESSION_KEY)
    flash("Logged out", "alert-success")
    return redirect(url_for("oauth2.admin.login"))

def random_string(length: int = 64) -> str:
    """Generate a random string."""
    return "".join(
        random.choice(string.ascii_letters + string.digits + string.punctuation)
        for _idx in range(0, length))

def __response_types__(grant_types: tuple[str, ...]) -> tuple[str, ...]:
    """Compute response types from grant types."""
    resps = {
        "password": ("token",),
        "authorization_code": ("token", "code"),
        "refresh_token": ("token",)
    }
    return tuple(set(
        resp_typ for types_list
        in (types for grant, types in resps.items() if grant in grant_types)
        for resp_typ in types_list))

@admin.route("/register-client", methods=["GET", "POST"])
@is_admin
def register_client():
    """Register an OAuth2 client."""
    def __list_users__(conn):
        with db.cursor(conn) as cursor:
            cursor.execute("SELECT * FROM users")
            return tuple(
                User(uuid.UUID(row["user_id"]), row["email"], row["name"])
                for row in cursor.fetchall())
    if request.method == "GET":
        return render_template(
            "admin/register-client.html",
            scope=current_app.config["OAUTH2_SCOPE"],
            users=with_db_connection(__list_users__),
            current_user=session[SESSION_KEY]["user"])

    form = request.form
    raw_client_secret = random_string()
    default_redirect_uri = form["redirect_uri"]
    grant_types = form.getlist("grants[]")
    client = OAuth2Client(
        client_id = uuid.uuid4(),
        client_secret = hash_password(raw_client_secret),
        client_id_issued_at = datetime.now(tz=timezone.utc),
        client_secret_expires_at = datetime.fromtimestamp(0),
        client_metadata = {
            "client_name": "GN2 Dev Server",
            "token_endpoint_auth_method": [
                "client_secret_post", "client_secret_basic"],
            "client_type": "confidential",
            "grant_types": ["password", "authorization_code", "refresh_token"],
            "default_redirect_uri": default_redirect_uri,
            "redirect_uris": [default_redirect_uri] + form.get("other_redirect_uri", "").split(),
            "response_type": __response_types__(tuple(grant_types)),
            "scope": form.getlist("scope[]")
        },
        user = with_db_connection(partial(
            user_by_id, user_id=uuid.UUID(form["user"])))
    )
    client = with_db_connection(partial(save_client, the_client=client))
    return render_template(
        "admin/registered-client.html",
        client=client,
        client_secret = raw_client_secret)
