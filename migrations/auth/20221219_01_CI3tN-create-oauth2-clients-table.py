"""
create oauth2_clients table
"""

from yoyo import step

__depends__ = {'20221208_01_sSdHz-add-public-column-to-resources-table'}

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS oauth2_clients(
            client_id TEXT NOT NULL,
            client_secret TEXT NOT NULL,
            client_id_issued_at INTEGER NOT NULL,
            client_secret_expires_at INTEGER NOT NULL,
            client_metadata TEXT,
            user_id TEXT NOT NULL,
            PRIMARY KEY(client_id),
            FOREIGN KEY(user_id) REFERENCES users(user_id)
              ON UPDATE CASCADE ON DELETE RESTRICT
        ) WITHOUT ROWID
        """,
        "DROP TABLE IF EXISTS oauth2_clients")
]
