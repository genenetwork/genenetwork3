"""Authorisation exceptions"""

class AuthorisationError(Exception):
    """
    Top-level exception for the `gn3.auth.authorisation` package.

    All exceptions in this package should inherit from this class.
    """
    error_code: int = 400

class ForbiddenAccess(AuthorisationError):
    """Raised for forbidden access."""
    error_code: int = 403

class UserRegistrationError(AuthorisationError):
    """Raised whenever a user registration fails"""

class NotFoundError(AuthorisationError):
    """Raised whenever we try fetching (a/an) object(s) that do(es) not exist."""
    error_code: int = 404

class InvalidData(AuthorisationError):
    """
    Exception if user requests invalid data
    """
    error_code: int = 400

class InconsistencyError(AuthorisationError):
    """
    Exception raised due to data inconsistencies
    """
    error_code: int = 500

class PasswordError(AuthorisationError):
    """
    Raise in case of an error with passwords.
    """

class UsernameError(AuthorisationError):
    """
    Raise in case of an error with a user's name.
    """
