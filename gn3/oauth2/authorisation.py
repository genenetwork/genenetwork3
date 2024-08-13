"""Handle authorisation with auth server."""
from functools import wraps

from flask import request, jsonify, current_app as app

from gn3.oauth2 import jwks
from gn3.oauth2.errors import TokenValidationError


def require_token(func):
    """Check for and verify bearer token."""
    @wraps(func)
    def __auth__(*args, **kwargs):
        try:
            bearer = request.headers.get("Authorization", "")
            if bearer.startswith("Bearer"):
                # validate token and return it
                _extra, token = [item.strip() for item in bearer.split(" ")]
                _jwt = jwks.validate_token(
                    token,
                    jwks.fetch_jwks(app.config["AUTH_SERVER_URL"],
                                    "auth/public-jwks"))
                return func(*args, **{**kwargs, "auth_token": {"access_token": token, "jwt": _jwt}})
            error_message = "We expected a bearer token but did not get one."
        except TokenValidationError as _tve:
            app.logger.debug("Token validation failed.", exc_info=True)
            error_message = "The token was found to be invalid."

        return jsonify({
            "error": "TokenValidationError",
            "description": error_message
        }), 400

    return __auth__
