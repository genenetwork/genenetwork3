"""Handle application level errors."""
from flask import Flask, jsonify

from gn3.auth.authorisation.errors import AuthorisationError

def handle_authorisation_error(exc: AuthorisationError):
    """Handle AuthorisationError if not handled anywhere else."""
    return jsonify({
        "error": type(exc).__name__,
        "error_description": " :: ".join(exc.args)
    }), 500

def register_error_handlers(app: Flask):
    """Register application-level error handlers."""
    app.register_error_handler(AuthorisationError, handle_authorisation_error)
