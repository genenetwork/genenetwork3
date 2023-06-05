"""Handle application level errors."""
from sqlite3 import OperationalError
from flask import Flask, jsonify, current_app
from authlib.oauth2.rfc6749.errors import OAuth2Error

from gn3.auth.authorisation.errors import AuthorisationError

def handle_authorisation_error(exc: AuthorisationError):
    """Handle AuthorisationError if not handled anywhere else."""
    current_app.logger.error(exc)
    return jsonify({
        "error": type(exc).__name__,
        "error_description": " :: ".join(exc.args)
    }), exc.error_code

def handle_oauth2_errors(exc: OAuth2Error):
    """Handle OAuth2Error if not handled anywhere else."""
    current_app.logger.error(exc)
    return jsonify({
        "error": exc.error,
        "error_description": exc.description,
    }), exc.status_code

def handle_sqlite3_errors(exc: OperationalError):
    """Handle sqlite3 errors if not handled anywhere else."""
    current_app.logger.error(exc)
    return jsonify({
        "error": "DatabaseError",
        "error_description": exc.args[0],
    }), 500

def register_error_handlers(app: Flask):
    """Register application-level error handlers."""
    app.register_error_handler(OAuth2Error, handle_oauth2_errors)
    app.register_error_handler(OperationalError, handle_sqlite3_errors)
    app.register_error_handler(AuthorisationError, handle_authorisation_error)
