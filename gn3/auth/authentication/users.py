"""User-specific code and data structures."""
from uuid import UUID
from typing import NamedTuple

import bcrypt
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
    """Retrieve user from database by their email address"""
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        row = cursor.fetchone()

    if row:
        return Just(User(UUID(row["user_id"]), row["email"], row["name"]))

    return Nothing

def user_by_id(conn: db.DbConnection, user_id: UUID) -> Maybe:
    """Retrieve user from database by their user id"""
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM users WHERE user_id=?", (str(user_id),))
        row = cursor.fetchone()

    if row:
        return Just(User(UUID(row["user_id"]), row["email"], row["name"]))

    return Nothing

def valid_login(conn: db.DbConnection, user: User, password: str) -> bool:
    """Check the validity of the provided credentials for login."""
    with db.cursor(conn) as cursor:
        cursor.execute(
            ("SELECT * FROM users LEFT JOIN user_credentials "
             "ON users.user_id=user_credentials.user_id "
             "WHERE users.user_id=?"),
            (str(user.user_id),))
        row = cursor.fetchone()

    if row is None:
        return False

    return bcrypt.checkpw(password.encode("utf-8"), row["password"])
