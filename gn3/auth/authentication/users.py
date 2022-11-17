"""User-specific code and data structures."""
from uuid import UUID
from typing import NamedTuple

class User(NamedTuple):
    """Class representing a user."""
    user_id: UUID
    email: str
    name: str
