"""User-specific code and data structures."""
from uuid import UUID
from typing import NamedTuple

from pymonad.maybe import Just, Maybe, Nothing

from gn3.auth import db

class User(NamedTuple):
    """Class representing a user."""
    user_id: UUID
    email: str
    name: str

    def get_user_id(self):
        """Return the user's UUID. Mostly for use with Authlib."""
        return self.user_id

def user_by_email(conn: db.DbConnection, email: str) -> Maybe:
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        row = cursor.fetchone()

    if row:
        return Just(User(UUID(row["user_id"]), row["email"], row["name"]))

    return Nothing
