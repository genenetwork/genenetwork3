"""Endpoints for the oauth2 server"""
import uuid
import traceback

from authlib.oauth2.rfc6749.errors import InvalidClientError
from email_validator import validate_email, EmailNotValidError
from flask import (
    flash,
    request,
    url_for,
    redirect,
    Response,
    Blueprint,
    render_template,
    current_app as app)

from gn3.auth import db
from gn3.auth.db_utils import with_db_connection
from gn3.auth.authorisation.errors import ForbiddenAccess

from .resource_server import require_oauth
from .endpoints.revocation import RevocationEndpoint
from .endpoints.introspection import IntrospectionEndpoint

from ..users import valid_login, NotFoundError, user_by_email

auth = Blueprint("auth", __name__)

@auth.route("/delete-client/<uuid:client_id>", methods=["GET", "POST"])
def delete_client(client_id: uuid.UUID):
    """Delete an OAuth2 client."""
    return f"WOULD DELETE OAUTH2 CLIENT {client_id}."

@auth.route("/authorise", methods=["GET", "POST"])
def authorise():
    """Authorise a user"""
    try:
        server = app.config["OAUTH2_SERVER"]
        client_id = uuid.UUID(request.args.get(
            "client_id",
            request.form.get("client_id", str(uuid.uuid4()))))
        client = server.query_client(client_id)
        if not bool(client):
            flash("Invalid OAuth2 client.", "alert-error")
        if request.method == "GET":
            client = server.query_client(request.args.get("client_id"))
            return render_template(
                "oauth2/authorise-user.html",
                client=client,
                scope=client.scope,
                response_type="code")

        form = request.form
        def __authorise__(conn: db.DbConnection) -> Response:
            email_passwd_msg = "Email or password is invalid!"
            redirect_response = redirect(url_for("oauth2.auth.authorise",
                                                 client_id=client_id))
            try:
                email = validate_email(
                    form.get("user:email"), check_deliverability=False)
                user = user_by_email(conn, email["email"])
                if valid_login(conn, user, form.get("user:password", "")):
                    return server.create_authorization_response(request=request, grant_user=user)
                flash(email_passwd_msg, "alert-error")
                return redirect_response # type: ignore[return-value]
            except EmailNotValidError as _enve:
                app.logger.debug(traceback.format_exc())
                flash(email_passwd_msg, "alert-error")
                return redirect_response # type: ignore[return-value]
            except NotFoundError as _nfe:
                app.logger.debug(traceback.format_exc())
                flash(email_passwd_msg, "alert-error")
                return redirect_response # type: ignore[return-value]

        return with_db_connection(__authorise__)
    except InvalidClientError as ice:
        return render_template(
            "oauth2/oauth2_error.html", error=ice), ice.status_code

@auth.route("/token", methods=["POST"])
def token():
    """Retrieve the authorisation token."""
    server = app.config["OAUTH2_SERVER"]
    return server.create_token_response()

@auth.route("/revoke", methods=["POST"])
def revoke_token():
    """Revoke the token."""
    return app.config["OAUTH2_SERVER"].create_endpoint_response(
        RevocationEndpoint.ENDPOINT_NAME)

@auth.route("/introspect", methods=["POST"])
@require_oauth("introspect")
def introspect_token() -> Response:
    """Provide introspection information for the token."""
    # This is dangerous to provide publicly
    authorised_clients = app.config.get(
        "OAUTH2_CLIENTS_WITH_INTROSPECTION_PRIVILEGE", [])
    with require_oauth.acquire("introspect") as the_token:
        if the_token.client.client_id in authorised_clients:
            return app.config["OAUTH2_SERVER"].create_endpoint_response(
                IntrospectionEndpoint.ENDPOINT_NAME)

    raise ForbiddenAccess("You cannot access this endpoint")
