"""User-specific code and data structures."""
from uuid import UUID, uuid4
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

def save_user(cursor: db.DbCursor, email: str, name: str) -> User:
    """
    Create and persist a user.

    The user creation could be done during a transaction, therefore the function
    takes a cursor object rather than a connection.

    The newly created and persisted user is then returned.
    """
    user_id = uuid4()
    cursor.execute("INSERT INTO users VALUES (?, ?, ?)",
                   (str(user_id), email, name))
    return User(user_id, email, name)

def set_user_password(
        cursor: db.DbCursor, user: User, password: str) -> Tuple[User, bytes]:
    """Set the given user's password in the database."""
    hashed_password = bcrypt.hashpw(password.encode("utf8"), bcrypt.gensalt())
    cursor.execute(
        ("INSERT INTO user_credentials VALUES (:user_id, :hash) "
         "ON CONFLICT (user_id) DO UPDATE SET password=:hash"),
        {"user_id": str(user.user_id), "hash": hashed_password})
    return user, hashed_password
