"""Authorisation exceptions"""

class AuthorisationError(Exception):
    """
    Top-level exception for the `gn3.auth.authorisation` package.

    All exceptions in this package should inherit from this class.
    """
    error_code: int = 500

class UserRegistrationError(AuthorisationError):
    """Raised whenever a user registration fails"""
