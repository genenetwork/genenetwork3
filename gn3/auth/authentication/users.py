"""User-specific code and data structures."""
from uuid import UUID, uuid4
from typing import Any, Tuple, NamedTuple

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from gn3.auth import db
from gn3.auth.authorisation.errors import NotFoundError

class User(NamedTuple):
    """Class representing a user."""
    user_id: UUID
    email: str
    name: str

    def get_user_id(self):
        """Return the user's UUID. Mostly for use with Authlib."""
        return self.user_id

    def dictify(self) -> dict[str, Any]:
        """Return a dict representation of `User` objects."""
        return {"user_id": self.user_id, "email": self.email, "name": self.name}

DUMMY_USER = User(user_id=UUID("a391cf60-e8b7-4294-bd22-ddbbda4b3530"),
                  email="gn3@dummy.user",
                  name="Dummy user to use as placeholder")

def user_by_email(conn: db.DbConnection, email: str) -> User:
    """Retrieve user from database by their email address"""
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        row = cursor.fetchone()

    if row:
        return User(UUID(row["user_id"]), row["email"], row["name"])

    raise NotFoundError(f"Could not find user with email {email}")

def user_by_id(conn: db.DbConnection, user_id: UUID) -> User:
    """Retrieve user from database by their user id"""
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM users WHERE user_id=?", (str(user_id),))
        row = cursor.fetchone()

    if row:
        return User(UUID(row["user_id"]), row["email"], row["name"])

    raise NotFoundError(f"Could not find user with ID {user_id}")

def same_password(password: str, hashed: str) -> bool:
    """Check that `raw_password` is hashed to `hash`"""
    try:
        return hasher().verify(hashed, password)
    except VerifyMismatchError as _vme:
        return False

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

    return same_password(password, row["password"])

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

def hasher():
    """Retrieve PasswordHasher object"""
    # TODO: Maybe tune the parameters here...
    # Tuneable Parameters:
    # - time_cost (default: 2)
    # - memory_cost (default: 102400)
    # - parallelism (default: 8)
    # - hash_len (default: 16)
    # - salt_len (default: 16)
    # - encoding (default: 'utf-8')
    # - type (default: <Type.ID: 2>)
    return PasswordHasher()

def hash_password(password):
    """Hash the password."""
    return hasher().hash(password)

def set_user_password(
        cursor: db.DbCursor, user: User, password: str) -> Tuple[User, bytes]:
    """Set the given user's password in the database."""
    hashed_password = hash_password(password)
    cursor.execute(
        ("INSERT INTO user_credentials VALUES (:user_id, :hash) "
         "ON CONFLICT (user_id) DO UPDATE SET password=:hash"),
        {"user_id": str(user.user_id), "hash": hashed_password})
    return user, hashed_password

def users(conn: db.DbConnection,
          ids: tuple[UUID, ...] = tuple()) -> tuple[User, ...]:
    """
    Fetch all users with the given `ids`. If `ids` is empty, return ALL users.
    """
    params = ", ".join(["?"] * len(ids))
    with db.cursor(conn) as cursor:
        query = "SELECT * FROM users" + (
            f" WHERE user_id IN ({params})"
            if len(ids) > 0 else "")
        print(query)
        cursor.execute(query, tuple(str(the_id) for the_id in ids))
        return tuple(User(UUID(row["user_id"]), row["email"], row["name"])
                     for row in cursor.fetchall())
    return tuple()
