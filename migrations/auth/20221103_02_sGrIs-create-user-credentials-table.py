"""
create user_credentials table
"""

from yoyo import step

__depends__ = {'20221103_01_js9ub-initialise-the-auth-entic-oris-ation-database'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS user_credentials(
            user_id TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(user_id)
              ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS user_credentials")
]
