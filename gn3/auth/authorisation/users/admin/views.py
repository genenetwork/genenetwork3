"""UI for admin stuff"""
import uuid
import json
import random
import string
from functools import partial
from datetime import datetime, timezone, timedelta

from email_validator import validate_email, EmailNotValidError
from flask import (
    flash,
    request,
    url_for,
    redirect,
    Blueprint,
    current_app,
    render_template)


from gn3 import session
from gn3.auth import db
from gn3.auth.db_utils import with_db_connection

from gn3.auth.authentication.oauth2.models.oauth2client import (
    save_client,
    OAuth2Client,
    oauth2_clients,
    client as oauth2_client,
    delete_client as _delete_client)
from gn3.auth.authentication.users import (
    User,
    user_by_id,
    valid_login,
    user_by_email,
    hash_password)

from .ui import is_admin

admin = Blueprint("admin", __name__)

@admin.before_request
def update_expires():
    """Update session expiration."""
    if session.session_info() and not session.update_expiry():
        flash("Session has expired. Logging out...", "alert-warning")
        session.clear_session_info()
        return redirect(url_for("oauth2.admin.login"))
    return None

@admin.route("/dashboard", methods=["GET"])
@is_admin
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
                session.update_session_info(
                    user=user._asdict(),
                    expires=(
                        datetime.now(tz=timezone.utc) + timedelta(minutes=10)))
                return redirect(url_for(next_uri))
            flash(error_message, "alert-danger")
            return login_page
    except EmailNotValidError as _enve:
        flash(error_message, "alert-danger")
        return login_page

@admin.route("/logout", methods=["GET"])
def logout():
    """Log out the admin."""
    if not session.session_info():
        flash("Not logged in.", "alert-info")
        return redirect(url_for("oauth2.admin.login"))
    session.clear_session_info()
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
            current_user=session.session_user())

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

def __parse_client__(sqlite3_row) -> dict:
    """Parse the client details into python datatypes."""
    return {
        **dict(sqlite3_row),
        "client_metadata": json.loads(sqlite3_row["client_metadata"])
    }

@admin.route("/list-client", methods=["GET"])
@is_admin
def list_clients():
    """List all registered OAuth2 clients."""
    return render_template(
        "admin/list-oauth2-clients.html",
        clients=with_db_connection(oauth2_clients))

@admin.route("/view-client/<uuid:client_id>", methods=["GET"])
@is_admin
def view_client(client_id: uuid.UUID):
    """View details of OAuth2 client with given `client_id`."""
    return render_template(
        "admin/view-oauth2-client.html",
        client=with_db_connection(partial(oauth2_client, client_id=client_id)),
        scope=current_app.config["OAUTH2_SCOPE"])

@admin.route("/edit-client", methods=["POST"])
@is_admin
def edit_client():
    """Edit the details of the given client."""
    form = request.form
    the_client = with_db_connection(partial(
        oauth2_client, client_id=uuid.UUID(form["client_id"])))
    if the_client.is_nothing():
        flash("No such client.", "alert-danger")
        return redirect(url_for("oauth2.admin.list_clients"))
    the_client = the_client.value
    client_metadata = {
        **the_client.client_metadata,
        "default_redirect_uri": form["default_redirect_uri"],
        "redirect_uris": list(set(
            [form["default_redirect_uri"]] +
            form["other_redirect_uris"].split("\r\n"))),
        "grants": form.getlist("grants[]"),
        "scope": form.getlist("scope[]")
    }
    with_db_connection(partial(save_client, the_client=OAuth2Client(
        the_client.client_id,
        the_client.client_secret,
        the_client.client_id_issued_at,
        the_client.client_secret_expires_at,
        client_metadata,
        the_client.user)))
    flash("Client updated.", "alert-success")
    return redirect(url_for("oauth2.admin.view_client",
                            client_id=the_client.client_id))

@admin.route("/delete-client", methods=["POST"])
@is_admin
def delete_client():
    """Delete the details of the client."""
    form = request.form
    the_client = with_db_connection(partial(
        oauth2_client, client_id=uuid.UUID(form["client_id"])))
    if the_client.is_nothing():
        flash("No such client.", "alert-danger")
        return redirect(url_for("oauth2.admin.list_clients"))
    the_client = the_client.value
    with_db_connection(partial(_delete_client, client=the_client))
    flash((f"Client '{the_client.client_metadata.client_name}' was deleted "
           "successfully."),
          "alert-success")
    return redirect(url_for("oauth2.admin.list_clients"))
