"""Handle application level errors."""
import traceback

from http.client import RemoteDisconnected
from urllib.error import URLError
from sqlite3 import OperationalError
from SPARQLWrapper.SPARQLExceptions import (
    EndPointInternalError,
    EndPointNotFound,
    QueryBadFormed,
    SPARQLWrapperException,
    URITooLong,
    Unauthorized
)
from werkzeug.exceptions import NotFound
from flask import Flask, jsonify, current_app
from authlib.oauth2.rfc6749.errors import OAuth2Error

from gn3.auth.authorisation.errors import AuthorisationError


def add_trace(exc: Exception, jsonmsg: dict) -> dict:
    """Add the traceback to the error handling object."""
    return {
        **jsonmsg,
        "error-trace": "".join(traceback.format_exception(exc))
    }


def page_not_found(pnf):
    """Generic 404 handler."""
    return jsonify(add_trace(pnf, {
        "error": pnf.name,
        "error_description": pnf.description
    })), 404


def internal_server_error(pnf):
    """Generic 404 handler."""
    return jsonify(add_trace(pnf, {
        "error": pnf.name,
        "error_description": pnf.description
    })), 500


def handle_authorisation_error(exc: AuthorisationError):
    """Handle AuthorisationError if not handled anywhere else."""
    current_app.logger.error(exc)
    return jsonify(add_trace(exc, {
        "error": type(exc).__name__,
        "error_description": " :: ".join(exc.args)
    })), exc.error_code


def handle_oauth2_errors(exc: OAuth2Error):
    """Handle OAuth2Error if not handled anywhere else."""
    current_app.logger.error(exc)
    return jsonify(add_trace(exc, {
        "error": exc.error,
        "error_description": exc.description,
    })), exc.status_code


def handle_sqlite3_errors(exc: OperationalError):
    """Handle sqlite3 errors if not handled anywhere else."""
    current_app.logger.error(exc)
    return jsonify({
        "error": "DatabaseError",
        "error_description": exc.args[0],
    }), 500


def handle_sparql_errors(exc: SPARQLWrapperException):
    """Handle sqlite3 errors if not handled anywhere else."""
    current_app.logger.error(exc)
    __code = {
        EndPointInternalError: 500,
        EndPointNotFound: 400,
        QueryBadFormed: 400,
        Unauthorized: 401,
        URITooLong: 414,
    }
    return jsonify({
        "error": exc.msg,
        "error_description": str(exc),
    }), __code.get(exc)


def register_error_handlers(app: Flask):
    """Register application-level error handlers."""
    app.register_error_handler(NotFound, page_not_found)
    app.register_error_handler(OAuth2Error, handle_oauth2_errors)
    app.register_error_handler(OperationalError, handle_sqlite3_errors)
    app.register_error_handler(AuthorisationError, handle_authorisation_error)
    app.register_error_handler(RemoteDisconnected, internal_server_error)
    app.register_error_handler(URLError, internal_server_error)
    for exc in (
            EndPointInternalError,
            EndPointNotFound,
            QueryBadFormed,
            URITooLong,
            Unauthorized
    ):
        app.register_error_handler(exc, handle_sparql_errors)
