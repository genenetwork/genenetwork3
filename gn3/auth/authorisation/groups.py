"""Handle the management of resource/user groups."""
import uuid

from gn3.auth import db
from .checks import authorised_p

@authorised_p(
    ("create-group",), success_message="Successfully created group.",
    error_message="Failed to create group.")
def create_group(conn, group_name):
    """Create a group"""
    with db.cursor(conn) as cursor:
        group_id = uuid.uuid4()
        cursor.execute(
            "INSERT INTO groups(group_id, group_name) VALUES (?, ?)",
            (str(group_id), group_name))
        return group_id
