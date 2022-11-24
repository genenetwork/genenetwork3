"""Functions to check for user authentication."""

from flask import g

from .exceptions import AuthenticationError

def authenticated_p(func):
    """Decorator for functions requiring authentication."""
    def __authenticated__(*args, **kwargs):
        user = g.user if hasattr(g, "user") else False
        if user:
            return func(*args, **kwargs)
        raise AuthenticationError("You need to be authenticated")
    return __authenticated__
