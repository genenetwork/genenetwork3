"""
Initialise the auth(entic|oris)ation database.
"""

from yoyo import step

__depends__ = {} # type: ignore[var-annotated]

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS users(
            user_id TEXT PRIMARY KEY NOT NULL,
            email TEXT UNIQUE NOT NULL,
            name TEXT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS users")
]
