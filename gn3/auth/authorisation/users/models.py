"""Functions for acting on users."""
import uuid

from gn3.auth import db
from gn3.auth.authorisation.checks import authorised_p

from gn3.auth.authentication.users import User

@authorised_p(
    ("system:user:list",),
    "You do not have the appropriate privileges to list users.",
    oauth2_scope="profile user")
def list_users(conn: db.DbConnection) -> tuple[User, ...]:
    """List out all users."""
    with db.cursor(conn) as cursor:
        cursor.execute("SELECT * FROM users")
        return tuple(
            User(uuid.UUID(row["user_id"]), row["email"], row["name"])
            for row in cursor.fetchall())
