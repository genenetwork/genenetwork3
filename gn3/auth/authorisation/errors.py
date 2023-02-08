"""Authorisation exceptions"""

class AuthorisationError(Exception):
    """
    Top-level exception for the `gn3.auth.authorisation` package.

    All exceptions in this package should inherit from this class.
    """
    error_code: int = 400

class UserRegistrationError(AuthorisationError):
    """Raised whenever a user registration fails"""

class NotFoundError(AuthorisationError):
    """Raised whenever we try fetching (a/an) object(s) that do(es) not exist."""
    error_code: int = 404

class InconsistencyError(AuthorisationError):
    """
    Exception raised due to data inconsistencies
    """
    error_code: int = 500
