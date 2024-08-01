"""List of possible errors."""

class AuthorisationError(Exception):
    """Top-level error class dealing with generic authorisation errors."""


class TokenValidationError(AuthorisationError):
    """Class to indicate that token validation failed."""
